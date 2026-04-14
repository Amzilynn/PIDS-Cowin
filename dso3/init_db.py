from dso3.database import engine
from dso3.models import delegate, product, recommendation

delegate.Base.metadata.create_all(bind=engine)
product.Base.metadata.create_all(bind=engine)
recommendation.Base.metadata.create_all(bind=engine)