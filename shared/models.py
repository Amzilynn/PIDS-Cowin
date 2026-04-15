from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, ForeignKey, TIMESTAMP, Enum, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Gamme(Base):
    __tablename__ = "gammes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    

    products = relationship("Product", back_populates="gamme")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    gamme_id = Column(Integer, ForeignKey("gammes.id"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text)  # Pour un résumé global court
    indications = Column(Text)  # Les indications médicales
    compositions = Column(Text) # Les principes actifs
    usage_advice = Column(Text) # Les conseils d'utilisation (posologie)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    gamme = relationship("Gamme", back_populates="products")
    simulations = relationship("Simulation", back_populates="product")

class Delegate(Base):
    __tablename__ = "delegates"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("Medical", "Commercial"), nullable=False, default="Medical")
    current_level = Column(Enum("Débutant", "Junior", "Confirmé","Expert"), default="Débutant")
    global_score = Column(Numeric(5, 2), default=0.00)
    total_simulations_completed = Column(Integer, default=0)
    last_login = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    

    simulations = relationship("Simulation", back_populates="delegate")
    # recommendations = relationship("Recommendation", back_populates="delegate")

class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    delegate_id = Column(Integer, ForeignKey("delegates.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    start_time = Column(TIMESTAMP, server_default=func.now())
    end_time = Column(TIMESTAMP, nullable=True)
    final_score = Column(Numeric(5, 2), nullable=True)
    

    delegate = relationship("Delegate", back_populates="simulations")
    product = relationship("Product", back_populates="simulations")
    messages = relationship("Message", back_populates="simulation", cascade="all, delete-orphan")
    evaluation = relationship("Evaluation", back_populates="simulation", uselist=False, cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id"), nullable=False)
    sender_type = Column(Enum("User", "Avatar"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    simulation = relationship("Simulation", back_populates="messages")
    audio = relationship("AudioAsset", back_populates="message", uselist=False, cascade="all, delete-orphan")

class AudioAsset(Base):
    __tablename__ = "audio_assets"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(BigInteger, ForeignKey("messages.id"), unique=True, nullable=False)
    file_path = Column(String(512), nullable=False)
    duration_ms = Column(Integer, nullable=False)
    format = Column(String(10), default="wav")
    created_at = Column(TIMESTAMP, server_default=func.now())

    message = relationship("Message", back_populates="audio")

class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id"), unique=True, nullable=False)
    
    # Behavioral Metrics
    confidence_score = Column(Numeric(3, 2))
    stress_score = Column(Numeric(3, 2))
    engagement_score = Column(Numeric(3, 2))
    posture_score = Column(Numeric(3, 2))
    eye_contact_rate = Column(Numeric(3, 2))
    
    # NLP Metrics
    product_knowledge_score = Column(Numeric(3, 2))
    vocabulary_richness = Column(Numeric(3, 2))
    
    dominant_emotion = Column(String(50))
    dominant_tone = Column(String(50))
    feedback_summary = Column(Text)
    
    improvement_areas = Column(JSON)
    
    created_at = Column(TIMESTAMP, server_default=func.now())

    simulation = relationship("Simulation", back_populates="evaluation")

"""
class Scenario(Base):
    __tablename__ = "scenarios"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    difficulty = Column(Enum("Easy", "Medium", "Hard"), default="Medium")
    persona_config = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())
    product = relationship("Product")
    simulations = relationship("Simulation", back_populates="scenario")

class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, index=True)
    delegate_id = Column(Integer, ForeignKey("delegates.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    reason = Column(Text, nullable=False)
    priority = Column(Integer, default=1)
    is_completed = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    delegate = relationship("Delegate", back_populates="recommendations")
    product = relationship("Product")
"""
