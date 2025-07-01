from graph import app

if __name__ == "__main__":
    question = "Generate python code for printing Hello World, and creating a list of numbers from 1 to 10 and printing this."
    result = app.invoke(
        {"messages": [("user", question)], "iterations": 0, "error": ""}
    )
    print(result)
