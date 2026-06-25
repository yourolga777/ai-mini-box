CLASSIFY_PROMPT = """Classify the message into exactly one of these categories:
- PRICES (Цены) — questions about price, cost, discounts, payment
- ORDER (Заказ) — placing an order, purchase, delivery status
- COMPLAINT (Жалоба) — complaints, problems, returns, defects
- SCHEDULE (График) — working hours, schedule, opening hours
- OTHER (Другое) — everything else

Message: {text}

Category:"""

DRAFT_PROMPT = """You are a customer support assistant for a small business.
Respond to the customer's message in a helpful and friendly manner.

Topic: {topic}
Customer message: {text}

{RAG_CONTEXT}

Your response:"""

DRAFT_PROMPT_NO_TOPIC = """You are a customer support assistant for a small business.
Respond to the customer's message in a helpful and friendly manner.

Customer message: {text}

{RAG_CONTEXT}

Your response:"""

EXTRACT_PROMPT = """Extract structured information from the message.
Return ONLY a valid JSON object with these fields if present:
- "phone": phone number
- "name": person or company name
- "order_id": order or invoice number
- "address": delivery or physical address
- "date": any date mentioned
If a field is not found, OMIT it from the output.

Message: {text}

JSON:"""

RAG_CONTEXT_TEMPLATE = """Relevant information from our knowledge base:
{context}"""
