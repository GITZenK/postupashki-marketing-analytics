from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    MetaData,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


metadata = MetaData(
    naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": (
            "fk_%(table_name)s_%(column_0_name)s_"
            "%(referred_table_name)s"
        ),
        "pk": "pk_%(table_name)s",
    }
)


class Base(DeclarativeBase):
    metadata = metadata


class CampaignGoal(str, enum.Enum):
    AWARENESS = "awareness"
    CONVERSION = "conversion"


class TouchEventType(str, enum.Enum):
    VIEW = "view"
    CLICK = "click"
    BOT_START = "bot_start"


class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    WON = "won"
    LOST = "lost"


class LeadEventType(str, enum.Enum):
    CONVERSATION_STARTED = "conversation_started"
    MANAGER_ASSIGNED = "manager_assigned"
    QUALIFIED = "qualified"
    OFFER_SENT = "offer_sent"
    WON = "won"
    LOST = "lost"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class AttributionModel(str, enum.Enum):
    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"


class MarketingActivity(Base):
    __tablename__ = "marketing_activity"

    campaign_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    campaign_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    planned_budget: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
    )

    goal: Mapped[CampaignGoal] = mapped_column(
        SAEnum(
            CampaignGoal,
            name="campaign_goal",
            native_enum=False,
        ),
        nullable=False,
    )

    placements: Mapped[list["Placement"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            (
                "end_at IS NULL "
                "OR start_at IS NULL "
                "OR end_at >= start_at"
            ),
            name="valid_date_range",
        ),
        CheckConstraint(
            (
                "planned_budget IS NULL "
                "OR planned_budget >= 0"
            ),
            name="non_negative_budget",
        ),
    )


class Creative(Base):
    __tablename__ = "creative"

    creative_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(255),
    )

    text: Mapped[str | None] = mapped_column(
        Text,
    )

    offer: Mapped[str | None] = mapped_column(
        String(255),
    )

    destination_url: Mapped[str | None] = mapped_column(
        Text,
    )

    placements: Mapped[list["Placement"]] = relationship(
        back_populates="creative",
    )


class Placement(Base):
    __tablename__ = "placement"

    placement_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    campaign_id: Mapped[str] = mapped_column(
        ForeignKey(
            "marketing_activity.campaign_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    creative_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            "creative.creative_id"
        ),
    )

    channel: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    publisher: Mapped[str | None] = mapped_column(
        String(255),
    )

    publication_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    tracking_token: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        default=lambda: uuid.uuid4().hex,
    )

    campaign: Mapped[MarketingActivity] = relationship(
        back_populates="placements",
    )

    creative: Mapped[Creative | None] = relationship(
        back_populates="placements",
    )

    touches: Mapped[list["UserTouch"]] = relationship(
        back_populates="placement",
    )

    __table_args__ = (
        CheckConstraint(
            "cost >= 0",
            name="non_negative_cost",
        ),
        Index(
            "ix_placement_campaign_publication",
            "campaign_id",
            "publication_at",
        ),
    )


class User(Base):
    __tablename__ = "app_user"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    telegram_user_hash: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    touches: Mapped[list["UserTouch"]] = relationship(
        back_populates="user",
    )

    leads: Mapped[list["Lead"]] = relationship(
        back_populates="user",
    )

    payments: Mapped[list["Payment"]] = relationship(
        back_populates="user",
    )


class UserTouch(Base):
    __tablename__ = "user_touch"

    touch_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "app_user.user_id"
        ),
    )

    anonymous_id: Mapped[str | None] = mapped_column(
        String(128),
    )

    placement_id: Mapped[str] = mapped_column(
        ForeignKey(
            "placement.placement_id"
        ),
        nullable=False,
    )

    event_type: Mapped[TouchEventType] = mapped_column(
        SAEnum(
            TouchEventType,
            name="touch_event_type",
            native_enum=False,
        ),
        nullable=False,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    external_event_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
    )

    user: Mapped[User | None] = relationship(
        back_populates="touches",
    )

    placement: Mapped[Placement] = relationship(
        back_populates="touches",
    )

    attributions: Mapped[list["PaymentAttribution"]] = relationship(
        back_populates="touch",
    )

    __table_args__ = (
        CheckConstraint(
            (
                "user_id IS NOT NULL "
                "OR anonymous_id IS NOT NULL"
            ),
            name="touch_has_identity",
        ),
        Index(
            "ix_user_touch_user_time",
            "user_id",
            "occurred_at",
        ),
        Index(
            "ix_user_touch_anonymous_time",
            "anonymous_id",
            "occurred_at",
        ),
        Index(
            "ix_user_touch_placement_time",
            "placement_id",
            "occurred_at",
        ),
    )


class Lead(Base):
    __tablename__ = "lead"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "app_user.user_id"
        ),
        nullable=False,
    )

    status: Mapped[LeadStatus] = mapped_column(
        SAEnum(
            LeadStatus,
            name="lead_status",
            native_enum=False,
        ),
        nullable=False,
        default=LeadStatus.NEW,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(
        back_populates="leads",
    )

    events: Mapped[list["LeadEvent"]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
        order_by="LeadEvent.occurred_at",
    )

    __table_args__ = (
        Index(
            "ix_lead_user_created",
            "user_id",
            "created_at",
        ),
    )


class LeadEvent(Base):
    __tablename__ = "lead_event"

    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "lead.lead_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    event_type: Mapped[LeadEventType] = mapped_column(
        SAEnum(
            LeadEventType,
            name="lead_event_type",
            native_enum=False,
        ),
        nullable=False,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    manager_id: Mapped[str | None] = mapped_column(
        String(100),
    )

    lead: Mapped[Lead] = relationship(
        back_populates="events",
    )

    __table_args__ = (
        Index(
            "ix_lead_event_lead_time",
            "lead_id",
            "occurred_at",
        ),
    )


class Payment(Base):
    __tablename__ = "payment"

    payment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    order_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "app_user.user_id"
        ),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="RUB",
    )

    course: Mapped[str | None] = mapped_column(
        String(255),
    )

    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(
            PaymentStatus,
            name="payment_status",
            native_enum=False,
        ),
        nullable=False,
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    external_payment_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
    )

    user: Mapped[User] = relationship(
        back_populates="payments",
    )

    refunds: Mapped[list["Refund"]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
    )

    attributions: Mapped[list["PaymentAttribution"]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "amount >= 0",
            name="non_negative_amount",
        ),
        Index(
            "ix_payment_user_paid",
            "user_id",
            "paid_at",
        ),
        Index(
            "ix_payment_status_paid",
            "status",
            "paid_at",
        ),
    )

    @property
    def refunded_amount(self) -> Decimal:
        return sum(
            (
                refund.amount
                for refund in self.refunds
            ),
            Decimal("0.00"),
        )

    @property
    def net_amount(self) -> Decimal:
        return (
            self.amount
            - self.refunded_amount
        )


class Refund(Base):
    __tablename__ = "refund"

    refund_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    payment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "payment.payment_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    refunded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    reason: Mapped[str | None] = mapped_column(
        String(500),
    )

    payment: Mapped[Payment] = relationship(
        back_populates="refunds",
    )

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="positive_refund_amount",
        ),
        Index(
            "ix_refund_payment_time",
            "payment_id",
            "refunded_at",
        ),
    )


class PaymentAttribution(Base):
    __tablename__ = "payment_attribution"

    attribution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    payment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "payment.payment_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    touch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "user_touch.touch_id"
        ),
        nullable=False,
    )

    model: Mapped[AttributionModel] = mapped_column(
        SAEnum(
            AttributionModel,
            name="attribution_model",
            native_enum=False,
        ),
        nullable=False,
    )

    weight: Mapped[Decimal] = mapped_column(
        Numeric(8, 6),
        nullable=False,
    )

    attribution_window_days: Mapped[int] = mapped_column(
        nullable=False,
        default=30,
    )

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    payment: Mapped[Payment] = relationship(
        back_populates="attributions",
    )

    touch: Mapped[UserTouch] = relationship(
        back_populates="attributions",
    )

    __table_args__ = (
        UniqueConstraint(
            "payment_id",
            "touch_id",
            "model",
            name="payment_touch_model",
        ),
        CheckConstraint(
            "weight > 0 AND weight <= 1",
            name="valid_weight",
        ),
        CheckConstraint(
            "attribution_window_days > 0",
            name="positive_window",
        ),
        Index(
            "ix_attribution_payment_model",
            "payment_id",
            "model",
        ),
        Index(
            "ix_attribution_touch",
            "touch_id",
        ),
    )