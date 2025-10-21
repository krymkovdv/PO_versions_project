from schemas import TractorsSchema
f



@app.get("/tractors/", response_model=list[TractorsSchema])
def get_tractors(session: Session = Depends(get_session)):
    tractors = session.execute(select(Tractors)).scalars().all()
    return tractors  # FastAPI автоматически сериализует через Pydantic