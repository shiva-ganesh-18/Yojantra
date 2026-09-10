import sqlalchemy
from sqlalchemy import create_engine, text

def check():
    engine = create_engine('postgresql://schemematch:schemematch@localhost:5433/schemematch')
    with engine.connect() as conn:
        schemes = conn.execute(text("SELECT COUNT(*) FROM schemes")).scalar()
        print(f"Schemes count: {schemes}")
        institutions = conn.execute(text("SELECT COUNT(*) FROM institutions")).scalar()
        print(f"Institutions count: {institutions}")

        users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        print(f"Users count: {users}")
        csc = conn.execute(text("SELECT COUNT(*) FROM csc_centers")).scalar()
        print(f"CSC centers count: {csc}")

if __name__ == '__main__':
    check()
