from inventory import *

# Add products
add_product("Mountain Bike", "bike", "adult", 20000, 25000, 5)
add_product("Kids Bike", "bike", "kids", 10000, 14000, 3)
add_product("Helmet", "accessory", "safety", 2000, 3500, 10)

# Restock
restock_product(1, 5)

# Reduce stock
reduce_stock(2, 1)

# View all products
products = get_all_products()
print("\n📦 ALL PRODUCTS:")
for p in products:
    print(p)

# Low stock check
low = get_low_stock()
print("\n⚠️ LOW STOCK:")
for l in low:
    print(l)