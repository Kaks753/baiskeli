from auth import create_user, login

# Create users
# create_user("admin", "admin123", "admin")
# create_user("cashier1", "1234", "cashier")

# Test login
user = login("admin", "admin123")

if user:
    print("Logged in as:", user["role"])