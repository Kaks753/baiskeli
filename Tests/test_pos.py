from pos import process_sale, generate_receipt

cart = [
    {"product_id": 1, "quantity": 1},
    {"product_id": 3, "quantity": 0}
]

try:
    sale_id, total, items = process_sale(cart, payment_method="cash")
    
    receipt = generate_receipt(sale_id, total, items)
    print(receipt)

except Exception as e:
    print(e)