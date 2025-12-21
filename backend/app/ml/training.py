import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib # For saving/loading models
import os

from app.core.config import settings
from app.database import get_db
from app.models.transaction import Transaction # Example model for data fetching

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(settings.LOG_LEVEL)

class MLModelTrainer:
    """
    Manages the training, evaluation, and saving of machine learning models
    for various analytical and predictive tasks within the platform.

    This class supports a modular approach to ML model lifecycle, allowing
    different models for different use cases (e.g., sales forecasting,
    customer churn prediction, financing eligibility).
    """

    def __init__(self, model_name: str = "sales_forecaster"):
        """
        Initializes the MLModelTrainer with a specific model name.

        Args:
            model_name (str): The logical name of the model to be trained.
                              Used for distinguishing models and their saved files.
        """
        self.model_name = model_name
        self.model = None
        self.model_path = os.path.join(settings.ML_MODEL_SAVE_PATH, f"{self.model_name}.joblib")
        logger.info(f"MLModelTrainer initialized for model: {self.model_name}")

        # Ensure the model save directory exists
        os.makedirs(settings.ML_MODEL_SAVE_PATH, exist_ok=True)


    async def fetch_training_data(self) -> pd.DataFrame:
        """
        Fetches historical data from the PostgreSQL database required for model training.
        This is a placeholder and should be extended based on specific model needs.

        For sales forecasting, it might fetch historical transaction data.
        For financing recommendations, it might fetch aggregated business metrics.

        Returns:
            pd.DataFrame: A pandas DataFrame containing the prepared training data.
                          Returns an empty DataFrame if no data is found or on error.
        """
        logger.info(f"Fetching training data for {self.model_name} from database.")
        data = []
        try:
            # Use async session from FastAPI's dependency system (or direct async engine)
            async for session in get_db():
                # Example: Fetching a simplified set of transactions for demonstration
                # In a real scenario, this would involve more complex queries,
                # aggregations, and feature engineering.
                transactions = await session.execute(
                    Transaction.__table__.select().order_by(Transaction.transaction_date.asc())
                )
                for transaction in transactions.scalars().all():
                    data.append({
                        "transaction_date": transaction.transaction_date,
                        "amount": transaction.amount,
                        "product_category": transaction.product_category, # Example feature
                        # Add other relevant features from transactions or related tables
                    })
                logger.info(f"Fetched {len(data)} records for training.")

        except Exception as e:
            logger.error(f"Error fetching training data: {e}", exc_info=True)
            return pd.DataFrame() # Return empty DataFrame on error

        if not data:
            logger.warning("No data found for training.")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        # Example: Basic feature engineering for sales forecasting (e.g., total daily sales)
        # This part will be highly dependent on the specific ML task.
        if self.model_name == "sales_forecaster":
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            df = df.set_index('transaction_date').resample('D')['amount'].sum().reset_index()
            df.rename(columns={'amount': 'daily_sales'}, inplace=True)
            # Add lag features, rolling averages, etc., for time series forecasting
            df['day_of_week'] = df['transaction_date'].dt.dayofweek
            df['month'] = df['transaction_date'].dt.month
            df['lag_1_day_sales'] = df['daily_sales'].shift(1)
            df.dropna(inplace=True) # Drop rows with NaNs created by lag features
            logger.info(f"Prepared data for sales forecaster with {df.shape[0]} samples.")

        return df

    def preprocess_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Performs data preprocessing, including feature selection, handling missing values,
        and splitting data into features (X) and target (y).

        Args:
            df (pd.DataFrame): The raw data fetched from the database.

        Returns:
            tuple[pd.DataFrame, pd.Series]: A tuple containing the preprocessed
                                            features (X) and target (y).
        Raises:
            ValueError: If the DataFrame is empty or essential columns are missing.
        """
        if df.empty:
            raise ValueError("Cannot preprocess empty DataFrame.")

        # This part is highly dependent on the model's target and features.
        # Example for 'sales_forecaster':
        if self.model_name == "sales_forecaster":
            features = ['day_of_week', 'month', 'lag_1_day_sales']
            target = 'daily_sales'

            for col in features + [target]:
                if col not in df.columns:
                    raise ValueError(f"Missing required column for '{self.model_name}': {col}")

            X = df[features]
            y = df[target]

            logger.info(f"Data preprocessed: X shape {X.shape}, y shape {y.shape}")
            return X, y
        else:
            # Default or error case for other models
            raise NotImplementedError(f"Preprocessing for model '{self.model_name}' not implemented.")


    def train_model(self, X: pd.DataFrame, y: pd.Series) -> Any:
        """
        Trains the machine learning model using the provided features and target.
        The choice of model (e.g., Linear Regression, RandomForest) can be
        dynamic or based on the `model_name`.

        Args:
            X (pd.DataFrame): Training features.
            y (pd.Series): Target variable.

        Returns:
            Any: The trained machine learning model object.
        Raises:
            ValueError: If X or y are empty.
        """
        if X.empty or y.empty:
            raise ValueError("Cannot train with empty features or target data.")

        logger.info(f"Starting training for model: {self.model_name}")

        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        if self.model_name == "sales_forecaster":
            # Example: Using RandomForestRegressor for sales forecasting
            model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            model.fit(X_train, y_train)
            logger.info("RandomForestRegressor trained.")
        # Add more `elif` conditions for other model types
        # elif self.model_name == "customer_churn_predictor":
        #     model = LogisticRegression()
        #     model.fit(X_train, y_train)
        else:
            logger.warning(f"No specific model implementation for '{self.model_name}'. Using Linear Regression as default.")
            model = LinearRegression()
            model.fit(X_train, y_train)

        self.model = model
        self._evaluate_model(model, X_test, y_test)
        return model

    def _evaluate_model(self, model: Any, X_test: pd.DataFrame, y_test: pd.Series):
        """
        Evaluates the trained model on the test set and logs performance metrics.

        Args:
            model (Any): The trained model.
            X_test (pd.DataFrame): Test features.
            y_test (pd.Series): True target values for the test set.
        """
        logger.info(f"Evaluating model: {self.model_name}")
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        logger.info(f"Model '{self.model_name}' Evaluation Metrics:")
        logger.info(f"  Mean Squared Error (MSE): {mse:.4f}")
        logger.info(f"  R-squared (R2): {r2:.4f}")

        # You might want to store these metrics in a database or a tracking system (e.g., MLflow)

    def save_model(self, model: Any):
        """
        Saves the trained model to disk using joblib.

        Args:
            model (Any): The trained model object to save.
        """
        if model is None:
            logger.warning("No model to save. Training must be run first.")
            return

        try:
            joblib.dump(model, self.model_path)
            logger.info(f"Model '{self.model_name}' saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to save model '{self.model_name}': {e}", exc_info=True)


    async def run_training_pipeline(self):
        """
        Executes the full training pipeline: fetches data, preprocesses, trains,
        evaluates, and saves the model.
        """
        logger.info(f"Initiating full training pipeline for model: {self.model_name}")
        try:
            df_raw = await self.fetch_training_data()
            if df_raw.empty:
                logger.warning("Training pipeline aborted: No data available.")
                return

            X, y = self.preprocess_data(df_raw)
            trained_model = self.train_model(X, y)
            self.save_model(trained_model)
            logger.info(f"Training pipeline completed successfully for model: {self.model_name}")
            return True
        except ValueError as ve:
            logger.error(f"Training pipeline failed due to data issue: {ve}", exc_info=True)
            return False
        except NotImplementedError as nie:
            logger.error(f"Training pipeline failed: {nie}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during training pipeline for {self.model_name}: {e}", exc_info=True)
            return False

# Example usage (for testing or direct execution, typically called via Celery task)
if __name__ == "__main__":
    import asyncio
    from app.core.logging import setup_logging # Assume setup_logging exists

    setup_logging()

    async def main():
        """
        Main function to run the training pipeline for demonstration.
        """
        logger.info("Starting ML training demonstration...")
        trainer = MLModelTrainer(model_name="sales_forecaster")
        success = await trainer.run_training_pipeline()
        if success:
            logger.info("ML model training demo finished successfully!")
        else:
            logger.error("ML model training demo failed.")

    # To run this, ensure your database and environment variables are set up.
    # This might require mocking the database session for standalone testing.
    # For a full test, run `docker compose up` and then `docker exec` into the backend container
    # and execute `python app/ml/training.py`
    asyncio.run(main())