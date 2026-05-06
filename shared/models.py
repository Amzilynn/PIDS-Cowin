from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, ForeignKey, TIMESTAMP, Enum, JSON, BigInteger, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


# =============================================================================
# TABLE PARENTE : User (Joined Table Inheritance)
# Contient les infos de connexion communes à tous les types d'utilisateurs
# =============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    # type détermine vers quelle table enfant aller chercher les infos
    type = Column(Enum("delegue", "medecin", "pharmacien", "admin"), nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(TIMESTAMP, nullable=True)
    last_seen_recommendation_id = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())

    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    # Discriminator pour SQLAlchemy — indique quelle classe utiliser
    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "user",
    }


# =============================================================================
# TABLE ENFANT : Delegate (hérite de User)
# Colonnes métier du délégué — email/password_hash sont dans users
# =============================================================================

class Delegate(User):
    __tablename__ = "delegates"

    # Clé étrangère vers la table parente users
    id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    # role = sous-type de délégué (Medical ou Commercial)
    role = Column(Enum("Medical", "Commercial"), nullable=False, default="Medical")
    current_level = Column(Enum("Débutant", "Junior", "Confirmé", "Expert"), default="Débutant")
    global_score = Column(Numeric(5, 2), default=0.00)
    total_simulations_completed = Column(Integer, default=0)
    
    # DSO4 Fields
    address = Column(String(500), nullable=True)
    phone = Column(String(30), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Champs DSO3
    expertise = Column(Text, nullable=True)

    simulations = relationship("Simulation", back_populates="delegate")
    recommendations = relationship("Recommendation", back_populates="delegate")
    visites = relationship("Visit", back_populates="delegate")

    __mapper_args__ = {
        "polymorphic_identity": "delegue",
    }


# =============================================================================
# TABLE ENFANT : Medecin (hérite de User)
# Colonnes issues du fichier medecins.csv :
#   nom, prenom, specialite, telephone, email (→ dans users), adresse, lat, lng
# =============================================================================

class Medecin(User):
    __tablename__ = "medecins"

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    nom = Column(String(150), nullable=False)
    prenom = Column(String(150), nullable=True)
    specialite = Column(String(150), nullable=True)
    telephone = Column(String(30), nullable=True)
    adresse = Column(String(300), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    visites = relationship("Visit", back_populates="medecin")

    __mapper_args__ = {
        "polymorphic_identity": "medecin",
    }


# =============================================================================
# TABLE ENFANT : Pharmacien (hérite de User)
# Colonnes issues du fichier pharmacies.csv :
#   nom, type(jour/nuit), telephone, adresse, gouvernorat, url
# Note : email absent du CSV → généré automatiquement au format nom@avalive.tn
# =============================================================================

class Pharmacien(User):
    __tablename__ = "pharmaciens"

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    nom = Column(String(150), nullable=False)
    # type_pharmacie pour ne pas confondre avec le type d'utilisateur (users.type)
    type_pharmacie = Column(Enum("jour", "nuit"), nullable=True, default="jour")
    telephone = Column(String(30), nullable=True)
    adresse = Column(String(300), nullable=True)
    gouvernorat = Column(String(100), nullable=True)
    url = Column(String(512), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    visites = relationship("Visit", back_populates="pharmacien")

    __mapper_args__ = {
        "polymorphic_identity": "pharmacien",
    }


# =============================================================================
# TABLE ENFANT : Admin (hérite de User)
# Table minimale — toutes les infos sont dans users
# =============================================================================

class Admin(User):
    __tablename__ = "admins"

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    # Nom d'affichage de l'admin
    display_name = Column(String(150), nullable=True, default="Administrateur")

    __mapper_args__ = {
        "polymorphic_identity": "admin",
    }


# =============================================================================
# TABLES MÉTIER (inchangées)
# =============================================================================

from sqlalchemy import Date, Time

class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True)
    delegate_id = Column(Integer, ForeignKey("delegates.id"), nullable=False, index=True)
    medecin_id = Column(Integer, ForeignKey("medecins.id"), nullable=True, index=True)
    pharmacien_id = Column(Integer, ForeignKey("pharmaciens.id"), nullable=True, index=True)
    
    date = Column(Date, nullable=False)
    scheduled_time = Column(String(10), nullable=True)  # Format HH:MM
    duration_min = Column(Integer, nullable=True)
    status = Column(Enum("Prévue", "Effectuée", "Annulée", "Reportée", name="visit_status_enum"), default="Prévue")
    visit_type = Column(Enum("Physique", "En ligne", name="visit_type_enum"), default="Physique")
    
    distance_km = Column(Float, nullable=True)
    travel_time_min = Column(Float, nullable=True)
    score = Column(Numeric(4, 2), nullable=True)
    
    created_at = Column(TIMESTAMP, server_default=func.now())

    delegate = relationship("Delegate", back_populates="visites")
    medecin = relationship("Medecin", back_populates="visites")
    pharmacien = relationship("Pharmacien", back_populates="visites")


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
    category = Column(String(150), nullable=True)  # Ajouté par DSO3
    description = Column(Text)
    indications = Column(Text)
    compositions = Column(Text)
    usage_advice = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    gamme = relationship("Gamme", back_populates="products")
    simulations = relationship("Simulation", back_populates="product")
    recommendations = relationship("Recommendation", back_populates="product")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    delegate_id = Column(Integer, ForeignKey("delegates.id"), nullable=False, index=True)
    score = Column(Float, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    delegate = relationship("Delegate", back_populates="recommendations")
    product = relationship("Product", back_populates="recommendations")


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    delegate_id = Column(Integer, ForeignKey("delegates.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    start_time = Column(TIMESTAMP, server_default=func.now())
    end_time = Column(TIMESTAMP, nullable=True)
    final_score = Column(Numeric(5, 2), nullable=True)
    report_path = Column(String(512), nullable=True)

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


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info")  # recommendation, system, etc.
    is_read = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="notifications")
