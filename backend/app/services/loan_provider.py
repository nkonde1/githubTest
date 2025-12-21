import random

class LoanProviderService:
    def get_offers(self, credit_score: int, region: str = "DE") -> list:
        """
        Returns a list of simulated loan offers based on credit score and region.
        Simulates fetching from an open source API or aggregator.
        """
        offers = []
        
        # Base offers available to everyone
        if credit_score >= 300:
            offers.append({
                "provider": "MicroStart DE",
                "loan_name": "Starter Capital",
                "amount_range": {"min": 1000, "max": 10000},
                "interest_rate": 12.5,
                "term_months": [12, 24],
                "requirements": ["Business registration"],
                "logo_url": "https://ui-avatars.com/api/?name=MicroStart&background=random"
            })

        # Fair credit offers
        if credit_score >= 600:
            offers.append({
                "provider": "CommerzFinanz",
                "loan_name": "SME Growth Loan",
                "amount_range": {"min": 10000, "max": 50000},
                "interest_rate": 8.9,
                "term_months": [12, 24, 36, 48],
                "requirements": ["6 months revenue > 5k"],
                "logo_url": "https://ui-avatars.com/api/?name=Commerz&background=002f6c&color=fff"
            })
            
        # Good credit offers
        if credit_score >= 700:
            offers.append({
                "provider": "Deutsche BizBank",
                "loan_name": "Premium Business Credit",
                "amount_range": {"min": 50000, "max": 250000},
                "interest_rate": 4.5,
                "term_months": [24, 36, 60],
                "requirements": ["2 years in business", "Positive cash flow"],
                "logo_url": "https://ui-avatars.com/api/?name=DB&background=0018a8&color=fff"
            })
            
            offers.append({
                "provider": "TechLend Germany",
                "loan_name": "Digital Innovation Fund",
                "amount_range": {"min": 20000, "max": 100000},
                "interest_rate": 5.2,
                "term_months": [12, 24, 36],
                "requirements": ["Tech sector", "Online revenue"],
                "logo_url": "https://ui-avatars.com/api/?name=TechLend&background=00d4ff&color=000"
            })

        return offers
