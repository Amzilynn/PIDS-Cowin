from database import engine
from models import delegate, product, recommendation

delegate.Base.metadata.create_all(bind=engine)
product.Base.metadata.create_all(bind=engine)
recommendation.Base.metadata.create_all(bind=engine)