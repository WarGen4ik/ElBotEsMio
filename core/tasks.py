from bot.celery1 import app


@app.task
def test():
    print("hello")