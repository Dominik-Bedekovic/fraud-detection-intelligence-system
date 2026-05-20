from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.app.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    role = relationship("Role", back_populates="users")
    transactions = relationship("Transaction", back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    step = Column(Integer, default=1, nullable=False)
    type = Column(String(50), nullable=False)

    amount = Column(Float, nullable=False)

    # These column names are mapped to the actual lowercase PostgreSQL column names.
    oldbalanceOrg = Column("oldbalanceorg", Float, nullable=False)
    newbalanceOrig = Column("newbalanceorig", Float, nullable=False)
    oldbalanceDest = Column("oldbalancedest", Float, nullable=False)
    newbalanceDest = Column("newbalancedest", Float, nullable=False)

    source = Column(String(20), default="single", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="transactions")
    prediction_result = relationship(
        "PredictionResult",
        back_populates="transaction",
        uselist=False,
    )


class PredictionResult(Base):
    __tablename__ = "prediction_results"

    id = Column(Integer, primary_key=True, index=True)

    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)

    prediction = Column(Integer, nullable=False)
    label = Column(String(50), nullable=False)
    probability = Column(Float, nullable=False)

    model_name = Column(String(100), nullable=True)
    model_version = Column(String(100), nullable=True)
    threshold = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    transaction = relationship("Transaction", back_populates="prediction_result")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")