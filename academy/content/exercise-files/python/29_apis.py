"""Working with APIs & JSON: the runnable examples from lesson 6.3 of the Complete Python Tutorial.

Run it with:  python3 29_apis.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# parse_api_response.py
# ----------------------------------------------------------------------
import json

# A typical API response body (as text)
body = """{
  "status": "success",
  "data": {
    "orders": [
      {"id": "ORD-1", "amount": 1499.0, "customer": {"name": "Anu"}, "items": 2},
      {"id": "ORD-2", "amount": 349.0,  "customer": {"name": "Rahul"}, "items": 1},
      {"id": "ORD-3", "amount": 2899.0, "customer": null, "items": 3}
    ],
    "page": 1, "has_more": false
  }
}"""
payload = json.loads(body)
orders = payload["data"]["orders"]
for o in orders:
    name = (o.get("customer") or {}).get("name", "Guest")      # handle null safely
    print(f"{o['id']}: {name:<6} ₹{o['amount']:,.2f}")
print("Revenue:", sum(o["amount"] for o in orders))
