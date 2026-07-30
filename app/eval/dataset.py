"""
Labeled evaluation dataset for retrieval quality assessment.
Each entry contains a query, expected relevant document sources, and expected answer keywords.
"""

EVAL_DATASET = [
    {
        "id": "q1",
        "query": "What are the parking rates at Downtown Garage?",
        "relevant_sources": ["pricing.md"],
        "expected_keywords": ["$3.00", "first hour", "$18.00", "daily"],
    },
    {
        "id": "q2",
        "query": "How do I book a parking spot?",
        "relevant_sources": ["booking_process.md"],
        "expected_keywords": ["reserve", "website", "app", "QR code"],
    },
    {
        "id": "q3",
        "query": "Where is the Riverside Lot located?",
        "relevant_sources": ["location_access.md", "general_info.md"],
        "expected_keywords": ["45 River Road", "Waterfront"],
    },
    {
        "id": "q4",
        "query": "Do you have EV charging stations?",
        "relevant_sources": ["general_info.md", "faq.md"],
        "expected_keywords": ["EV", "charging", "20", "Downtown"],
    },
    {
        "id": "q5",
        "query": "What is the cancellation policy?",
        "relevant_sources": ["booking_process.md", "faq.md"],
        "expected_keywords": ["2 hours", "free cancellation"],
    },
    {
        "id": "q6",
        "query": "Is there a shuttle service at the airport parking?",
        "relevant_sources": ["location_access.md", "general_info.md"],
        "expected_keywords": ["shuttle", "10 minutes", "terminal"],
    },
    {
        "id": "q7",
        "query": "What payment methods do you accept?",
        "relevant_sources": ["pricing.md"],
        "expected_keywords": ["credit", "debit", "Apple Pay", "Google Pay"],
    },
    {
        "id": "q8",
        "query": "What are your opening hours?",
        "relevant_sources": ["faq.md"],
        "expected_keywords": ["24/7", "365"],
    },
    {
        "id": "q9",
        "query": "Do you offer monthly parking passes?",
        "relevant_sources": ["pricing.md"],
        "expected_keywords": ["monthly", "$250", "$180", "$300"],
    },
    {
        "id": "q10",
        "query": "What should I do if the gate doesn't open?",
        "relevant_sources": ["faq.md"],
        "expected_keywords": ["intercom", "button", "assistance"],
    },
    {
        "id": "q11",
        "query": "How many parking spaces does the Downtown Garage have?",
        "relevant_sources": ["general_info.md"],
        "expected_keywords": ["500"],
    },
    {
        "id": "q12",
        "query": "What are the student discounts?",
        "relevant_sources": ["pricing.md"],
        "expected_keywords": ["20%", "student", "monthly"],
    },
]
