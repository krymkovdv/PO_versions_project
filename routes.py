from schemas import TractorSchema
from models import Tractors


@app.get("/tractors/", response_model=list[TractorSchema])
def get_tractors(session: Session = Depends(get_session)):
    stmt = select(Tractors)
    result = session.execute(stmt).scalars().all()
    return result