from app.db.database import engine, Base, SessionLocal
from app.db.models import Scan, Finding

# 1. Create the tables in the database
print("Creating database tables...")
Base.metadata.create_all(bind=engine)

# 2. Open a database session
db = SessionLocal()

try:
    # 3. Create a new Scan record
    new_scan = Scan(file_name="users.py")
    
    # 4. Create a Finding record attached to that scan
    new_finding = Finding(
        rule_id="SQL-001",
        severity="HIGH",
        message="Potential SQL Injection",
        line=42,
        file="users.py",
        scan=new_scan # SQLAlchemy automatically handles the foreign key ID!
    )

    # 5. Add to session and commit (save) to the database
    db.add(new_scan)
    db.add(new_finding)
    db.commit()
    print("Successfully saved to database!\n")

    # 6. Let's prove it worked by reading from the database
    saved_scan = db.query(Scan).first()
    print(f"Scan ID {saved_scan.id} for file '{saved_scan.file_name}' at {saved_scan.created_at}")
    
    for f in saved_scan.findings:
         print(f"  -> Finding: [{f.severity}] {f.rule_id} at line {f.line}, status: {f.status}, message: {f.message}")

finally:
    db.close()