from db import SessionLocal, Log

session = SessionLocal()
logs = session.query(Log).all()

for log in logs:
    print(f"{log.timestamp} | {log.url} → {log.result}")

session.close()
