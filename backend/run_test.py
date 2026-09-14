from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.seed.seed_data import seed_database
from app.policy.seed import seed_policies
from app.segmentation.seed import seed_segments, seed_segment_rules
from app.models.access_request import AccessRequest
from app.pep.evaluator import PEPEvaluator

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()
seed_database(db)
seed_policies(db)
seed_segments(db)
seed_segment_rules(db)

access_req = db.query(AccessRequest).filter(
    AccessRequest.source_segment == "Development",
    AccessRequest.network_type == "PUBLIC_WIFI"
).first()

result = PEPEvaluator.enforce_access(db, access_req.id)
print(result.model_dump_json())
