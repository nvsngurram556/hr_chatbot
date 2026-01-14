import pandas as pd

USERS_CSV = "/Users/satya/hr_chatbot/user_list/users.csv"

def authenticate_user(username: str, password: str):
    df = pd.read_csv(
        USERS_CSV,
        header=None,
        names=["username", "password", "name", "email"]
    )

    user = df[
        (df["username"] == username) &
        (df["password"] == password)
    ]

    if not user.empty:
        return {
            "username": user.iloc[0]["username"],
            "name": user.iloc[0]["name"],
            "email": user.iloc[0]["email"]
        }

    return None