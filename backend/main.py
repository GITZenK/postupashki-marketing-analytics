from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path 
import pandas as pd

from database import get_connection, init_db

# Hi everyone
BASE_XLSX_PATH = Path(__file__).resolve().parent.parent / "data" / "base.xlsx"


class UserCreate(BaseModel):
    telegram_user_id: str
    created_at: str

class EventCreate(BaseModel):
    user_id: int
    event_type: str
    placement_id: str | None = None
    created_at: str

class ManagerCreate(BaseModel):
    manager_id: str
    name: str

class LeadCreate(BaseModel):
    user_id: int
    manager_id: str | None = None
    status: str = "new"
    created_at: str

class PurchaseCreate(BaseModel):
    user_id: int
    lead_id: int | None = None
    product: str
    amount: float
    purchased_at: str

class CampaignCreate(BaseModel):
    campaign_id: str
    name: str
    channel: str
    start_at: str | None = None
    end_at: str | None = None
    budget: float = 0


class PlacementCreate(BaseModel):
    placement_id: str
    campaign_id: str
    platform: str
    channel_name: str | None = None
    creative_id: str | None = None
    published_at: str | None = None
    cost: float = 0
    impressions: int = 0

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"message": "Marketing MVP is running"}

@app.post("/campaigns")
def create_campaign(campaign: CampaignCreate):
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO campaigns (
                campaign_id,
                name,
                channel,
                start_at,
                end_at,
                budget
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                campaign.campaign_id,
                campaign.name,
                campaign.channel,
                campaign.start_at,
                campaign.end_at,
                campaign.budget,
            ),
        )

        connection.commit()

        return {
            "message": "Campaign created",
            "campaign_id": campaign.campaign_id,
        }

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        connection.close()

@app.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: str):
    connection = get_connection()

    campaign = connection.execute(
        "SELECT * FROM campaigns WHERE campaign_id = ?",
        (campaign_id,),
    ).fetchone()

    connection.close()

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found",
        )

    return dict(campaign)

@app.get("/campaigns")
def get_campaigns():
    connection = get_connection()

    campaigns = connection.execute(
        "SELECT * FROM campaigns"
    ).fetchall()

    connection.close()

    return [dict(campaign) for campaign in campaigns]


@app.post("/placements")
def create_placement(placement: PlacementCreate):
    connection = get_connection()

    try:
        connection.execute(
    """
    INSERT INTO placements (
        placement_id,
        campaign_id,
        platform,
        channel_name,
        creative_id,
        published_at,
        cost,
        impressions
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
        placement.placement_id,
        placement.campaign_id,
        placement.platform,
        placement.channel_name,
        placement.creative_id,
        placement.published_at,
        placement.cost,
        placement.impressions,
    ),
)
        connection.commit()

        return {
            "message": "Placement created",
            "placement_id": placement.placement_id,
        }

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        connection.close()


@app.get("/placements")
def get_placements():
    connection = get_connection()

    placements = connection.execute(
        "SELECT * FROM placements"
    ).fetchall()

    connection.close()

    return [dict(placement) for placement in placements]


@app.get("/placements/{placement_id}")
def get_placement(placement_id: str):
    connection = get_connection()

    placement = connection.execute(
        "SELECT * FROM placements WHERE placement_id = ?",
        (placement_id,),
    ).fetchone()

    connection.close()

    if placement is None:
        raise HTTPException(
            status_code=404,
            detail="Placement not found",
        )

    return dict(placement)

@app.post("/events")
def create_event(event: EventCreate):
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO events (
                user_id,
                event_type,
                placement_id,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                event.user_id,
                event.event_type,
                event.placement_id,
                event.created_at,
            ),
        )

        connection.commit()

        return {
            "message": "Event created",
        }

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        connection.close()


@app.get("/events")
def get_events():
    connection = get_connection()

    events = connection.execute(
        "SELECT * FROM events"
    ).fetchall()

    connection.close()

    return [dict(event) for event in events]

@app.post("/users")
def create_user(user: UserCreate):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO users (
                telegram_user_id,
                created_at
            )
            VALUES (?, ?)
            """,
            (
                user.telegram_user_id,
                user.created_at,
            ),
        )

        connection.commit()

        return {
            "message": "User created",
            "user_id": cursor.lastrowid,
        }

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        connection.close()


@app.get("/users")
def get_users():
    connection = get_connection()

    users = connection.execute(
        "SELECT * FROM users"
    ).fetchall()

    connection.close()

    return [dict(user) for user in users]

@app.post("/managers")
def create_manager(manager: ManagerCreate):
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO managers (
                manager_id,
                name
            )
            VALUES (?, ?)
            """,
            (
                manager.manager_id,
                manager.name,
            ),
        )

        connection.commit()

        return {
            "message": "Manager created",
            "manager_id": manager.manager_id,
        }

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        connection.close()

@app.post("/leads")
def create_lead(lead: LeadCreate):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO leads (
                user_id,
                manager_id,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                lead.user_id,
                lead.manager_id,
                lead.status,
                lead.created_at,
            ),
        )

        connection.commit()

        return {
            "message": "Lead created",
            "lead_id": cursor.lastrowid,
        }

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        connection.close()


@app.get("/leads")
def get_leads():
    connection = get_connection()

    leads = connection.execute(
        "SELECT * FROM leads"
    ).fetchall()

    connection.close()

    return [dict(lead) for lead in leads]

@app.post("/purchases")
def create_purchase(purchase: PurchaseCreate):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO purchases (
                user_id,
                lead_id,
                product,
                amount,
                purchased_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                purchase.user_id,
                purchase.lead_id,
                purchase.product,
                purchase.amount,
                purchase.purchased_at,
            ),
        )

        connection.commit()

        return {
            "message": "Purchase created",
            "purchase_id": cursor.lastrowid,
        }

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        connection.close()

@app.get("/purchases")
def get_purchases():
    connection = get_connection()

    purchases = connection.execute(
        "SELECT * FROM purchases"
    ).fetchall()

    connection.close()

    return [dict(purchase) for purchase in purchases]


@app.get("/analytics/campaigns")
def get_all_campaigns_analytics():
    connection = get_connection()

    try:
        campaigns = connection.execute(
            """
            SELECT campaign_id
            FROM campaigns
            ORDER BY campaign_id
            """
        ).fetchall()

        result = []

        for campaign in campaigns:
            campaign_id = campaign["campaign_id"]

            placements = connection.execute(
                """
                SELECT placement_id, cost, impressions
                FROM placements
                WHERE campaign_id = ?
                """,
                (campaign_id,),
            ).fetchall()

            placement_ids = [p["placement_id"] for p in placements]

            clicks = 0
            leads = 0
            purchases = 0
            revenue = 0

            if placement_ids:
                placeholders = ",".join("?" for _ in placement_ids)

                clicks = connection.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM events
                    WHERE event_type = 'click'
                    AND placement_id IN ({placeholders})
                    """,
                    placement_ids,
                ).fetchone()[0]

                leads = connection.execute(
                    f"""
                    SELECT COUNT(DISTINCT l.lead_id)
                    FROM leads l
                    JOIN events e ON e.user_id = l.user_id
                    WHERE e.event_type = 'click'
                    AND e.placement_id IN ({placeholders})
                    """,
                    placement_ids,
                ).fetchone()[0]

                purchases = connection.execute(
                    f"""
                    SELECT COUNT(DISTINCT p.purchase_id)
                    FROM purchases p
                    JOIN events e ON e.user_id = p.user_id
                    WHERE e.event_type = 'click'
                    AND e.placement_id IN ({placeholders})
                    """,
                    placement_ids,
                ).fetchone()[0]

                revenue = connection.execute(
                    f"""
                    SELECT COALESCE(SUM(p.amount), 0)
                    FROM purchases p
                    JOIN events e ON e.user_id = p.user_id
                    WHERE e.event_type = 'click'
                    AND e.placement_id IN ({placeholders})
                    """,
                    placement_ids,
                ).fetchone()[0]

            impressions = sum(p["impressions"] or 0 for p in placements)
            cost = sum(p["cost"] or 0 for p in placements)

            ctr = clicks / impressions * 100 if impressions else 0
            conversion_rate = leads / clicks * 100 if clicks else 0
            cpc = cost / clicks if clicks else 0
            cpa = cost / leads if leads else 0
            roi = (revenue - cost) / cost * 100 if cost else 0

            result.append({
                "campaign_id": campaign_id,
                "placements": len(placements),
                "impressions": impressions,
                "clicks": clicks,
                "ctr": round(ctr, 2),
                "leads": leads,
                "purchases": purchases,
                "cost": round(cost, 2),
                "revenue": round(revenue, 2),
                "conversion_rate": round(conversion_rate, 2),
                "cpc": round(cpc, 2),
                "cpa": round(cpa, 2),
                "roi": round(roi, 2),
            })

        return result

    finally:
        connection.close()


@app.get("/analytics/campaigns/{campaign_id}")
def get_campaign_analytics(campaign_id: str):
    connection = get_connection()

    try:
        campaign = connection.execute(
            """
            SELECT campaign_id, name
            FROM campaigns
            WHERE campaign_id = ?
            """,
            (campaign_id,),
        ).fetchone()

        if campaign is None:
            raise HTTPException(
                status_code=404,
                detail="Campaign not found",
            )

        placements = connection.execute(
            """
            SELECT
                p.placement_id,
                p.cost,
                p.impressions
            FROM placements p
            WHERE p.campaign_id = ?
            """,
            (campaign_id,),
        ).fetchall()

        placement_ids = [p["placement_id"] for p in placements]

        clicks = 0
        leads = 0
        purchases = 0
        revenue = 0

        if placement_ids:
            placeholders = ",".join("?" for _ in placement_ids)

            clicks = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM events
                WHERE event_type = 'click'
                AND placement_id IN ({placeholders})
                """,
                placement_ids,
            ).fetchone()[0]

            leads = connection.execute(
                f"""
                SELECT COUNT(DISTINCT l.lead_id)
                FROM leads l
                JOIN events e ON e.user_id = l.user_id
                WHERE e.event_type = 'click'
                AND e.placement_id IN ({placeholders})
                """,
                placement_ids,
            ).fetchone()[0]

            purchases = connection.execute(
                f"""
                SELECT COUNT(DISTINCT p.purchase_id)
                FROM purchases p
                JOIN events e ON e.user_id = p.user_id
                WHERE e.event_type = 'click'
                AND e.placement_id IN ({placeholders})
                """,
                placement_ids,
            ).fetchone()[0]

            revenue = connection.execute(
                f"""
                SELECT COALESCE(SUM(p.amount), 0)
                FROM purchases p
                JOIN events e ON e.user_id = p.user_id
                WHERE e.event_type = 'click'
                AND e.placement_id IN ({placeholders})
                """,
                placement_ids,
            ).fetchone()[0]

        impressions = sum(p["impressions"] or 0 for p in placements)
        cost = sum(p["cost"] or 0 for p in placements)

        ctr = clicks / impressions * 100 if impressions else 0
        conversion_rate = leads / clicks * 100 if clicks else 0
        cpc = cost / clicks if clicks else 0
        cpa = cost / leads if leads else 0
        roi = (revenue - cost) / cost * 100 if cost else 0

        return {
            "campaign_id": campaign["campaign_id"],
            "campaign_name": campaign["name"],
            "placements": len(placements),
            "impressions": impressions,
            "clicks": clicks,
            "ctr": round(ctr, 2),
            "leads": leads,
            "purchases": purchases,
            "cost": round(cost, 2),
            "revenue": round(revenue, 2),
            "conversion_rate": round(conversion_rate, 2),
            "cpc": round(cpc, 2),
            "cpa": round(cpa, 2),
            "roi": round(roi, 2),
        }

    finally:
        connection.close()


@app.get("/analytics/channels")
def get_channels_analytics():
    connection = get_connection()

    try:
        channels = connection.execute(
            """
            SELECT DISTINCT channel
            FROM campaigns
            ORDER BY channel
            """
        ).fetchall()

        result = []

        for channel_row in channels:
            channel = channel_row["channel"]

            placements = connection.execute(
                """
                SELECT
                    p.placement_id,
                    p.cost,
                    p.impressions
                FROM placements p
                JOIN campaigns c
                    ON c.campaign_id = p.campaign_id
                WHERE c.channel = ?
                """,
                (channel,),
            ).fetchall()

            placement_ids = [p["placement_id"] for p in placements]

            clicks = 0
            leads = 0
            purchases = 0
            revenue = 0

            if placement_ids:
                placeholders = ",".join("?" for _ in placement_ids)

                clicks = connection.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM events
                    WHERE event_type = 'click'
                    AND placement_id IN ({placeholders})
                    """,
                    placement_ids,
                ).fetchone()[0]

                leads = connection.execute(
                    f"""
                    SELECT COUNT(DISTINCT l.lead_id)
                    FROM leads l
                    JOIN events e ON e.user_id = l.user_id
                    WHERE e.event_type = 'click'
                    AND e.placement_id IN ({placeholders})
                    """,
                    placement_ids,
                ).fetchone()[0]

                purchases = connection.execute(
                    f"""
                    SELECT COUNT(DISTINCT p.purchase_id)
                    FROM purchases p
                    JOIN events e ON e.user_id = p.user_id
                    WHERE e.event_type = 'click'
                    AND e.placement_id IN ({placeholders})
                    """,
                    placement_ids,
                ).fetchone()[0]

                revenue = connection.execute(
                    f"""
                    SELECT COALESCE(SUM(p.amount), 0)
                    FROM purchases p
                    JOIN events e ON e.user_id = p.user_id
                    WHERE e.event_type = 'click'
                    AND e.placement_id IN ({placeholders})
                    """,
                    placement_ids,
                ).fetchone()[0]

            impressions = sum(p["impressions"] or 0 for p in placements)
            cost = sum(p["cost"] or 0 for p in placements)

            ctr = clicks / impressions * 100 if impressions else 0
            conversion_rate = leads / clicks * 100 if clicks else 0
            cpc = cost / clicks if clicks else 0
            cpa = cost / leads if leads else 0
            roi = (revenue - cost) / cost * 100 if cost else 0

            result.append({
                "channel": channel,
                "placements": len(placements),
                "impressions": impressions,
                "clicks": clicks,
                "ctr": round(ctr, 2),
                "leads": leads,
                "purchases": purchases,
                "cost": round(cost, 2),
                "revenue": round(revenue, 2),
                "conversion_rate": round(conversion_rate, 2),
                "cpc": round(cpc, 2),
                "cpa": round(cpa, 2),
                "roi": round(roi, 2),
            })

        return result

    finally:
        connection.close()

@app.get("/analytics/dashboard")
def get_dashboard_analytics():
    connection = get_connection()

    try:
        campaigns = connection.execute(
            """
            SELECT campaign_id
            FROM campaigns
            ORDER BY campaign_id
            """
        ).fetchall()

        total_impressions = 0
        total_clicks = 0
        total_leads = 0
        total_purchases = 0
        total_cost = 0
        total_revenue = 0

        for campaign in campaigns:
            campaign_id = campaign["campaign_id"]

            placements = connection.execute(
                """
                SELECT placement_id, cost, impressions
                FROM placements
                WHERE campaign_id = ?
                """,
                (campaign_id,),
            ).fetchall()

            placement_ids = [p["placement_id"] for p in placements]

            total_impressions += sum(
                p["impressions"] or 0 for p in placements
            )

            total_cost += sum(
                p["cost"] or 0 for p in placements
            )

            if not placement_ids:
                continue

            placeholders = ",".join("?" for _ in placement_ids)

            total_clicks += connection.execute(
                f"""
                SELECT COUNT(*)
                FROM events
                WHERE event_type = 'click'
                AND placement_id IN ({placeholders})
                """,
                placement_ids,
            ).fetchone()[0]

            total_leads += connection.execute(
                f"""
                SELECT COUNT(DISTINCT l.lead_id)
                FROM leads l
                JOIN events e ON e.user_id = l.user_id
                WHERE e.event_type = 'click'
                AND e.placement_id IN ({placeholders})
                """,
                placement_ids,
            ).fetchone()[0]

            total_purchases += connection.execute(
                f"""
                SELECT COUNT(DISTINCT p.purchase_id)
                FROM purchases p
                JOIN events e ON e.user_id = p.user_id
                WHERE e.event_type = 'click'
                AND e.placement_id IN ({placeholders})
                """,
                placement_ids,
            ).fetchone()[0]

            total_revenue += connection.execute(
                f"""
                SELECT COALESCE(SUM(p.amount), 0)
                FROM purchases p
                JOIN events e ON e.user_id = p.user_id
                WHERE e.event_type = 'click'
                AND e.placement_id IN ({placeholders})
                """,
                placement_ids,
            ).fetchone()[0]

        ctr = (
            total_clicks / total_impressions * 100
            if total_impressions
            else 0
        )

        conversion_rate = (
            total_leads / total_clicks * 100
            if total_clicks
            else 0
        )

        cpc = (
            total_cost / total_clicks
            if total_clicks
            else 0
        )

        cpa = (
            total_cost / total_leads
            if total_leads
            else 0
        )

        roi = (
            (total_revenue - total_cost) / total_cost * 100
            if total_cost
            else 0
        )

        return {
            "summary": {
                "impressions": total_impressions,
                "clicks": total_clicks,
                "ctr": round(ctr, 2),
                "leads": total_leads,
                "purchases": total_purchases,
                "cost": round(total_cost, 2),
                "revenue": round(total_revenue, 2),
                "conversion_rate": round(conversion_rate, 2),
                "cpc": round(cpc, 2),
                "cpa": round(cpa, 2),
                "roi": round(roi, 2),
            }
        }

    finally:
        connection.close()


@app.get("/analytics/sales")
def sales_analytics():
    connection = get_connection()

    revenue = connection.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM sales"
    ).fetchone()[0]

    purchases = connection.execute(
        "SELECT COUNT(*) FROM sales"
    ).fetchone()[0]

    customers = connection.execute(
        "SELECT COUNT(DISTINCT student_id) FROM sales"
    ).fetchone()[0]

    base_df = pd.read_excel(
        BASE_XLSX_PATH,
        usecols=["Курс"],
    )

    courses = int(
        base_df["Курс"]
        .dropna()
        .nunique()
    )

    average_check = (
        revenue / purchases
        if purchases
        else 0
    )

    repeat_customers = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT student_id
            FROM sales
            GROUP BY student_id
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    repeat_rate = (
        repeat_customers / customers * 100
        if customers
        else 0
    )

    connection.close()

    return {
        "revenue": revenue,
        "purchases": purchases,
        "customers": customers,
        "courses": courses,
        "average_check": average_check,
        "repeat_customers": repeat_customers,
        "repeat_rate": repeat_rate,
    }

@app.get("/analytics/attribution")
def analytics_attribution():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            sp.campaign_id,
            sc.name AS campaign_name,
            sp.placement_id,
            sp.channel_name,
            sp.creative_id,
            sp.cost,
            COUNT(DISTINCT mt.touch_id) AS touches,
            COUNT(
                DISTINCT CASE
                    WHEN mt.event_type = 'lead'
                    THEN mt.student_id
                END
            ) AS leads,
            COUNT(DISTINCT a.student_id) AS buyers,
            COALESCE(SUM(a.attributed_revenue), 0) AS revenue
        FROM synthetic_placements sp
        LEFT JOIN synthetic_campaigns sc
            ON sc.campaign_id = sp.campaign_id
        LEFT JOIN marketing_touches mt
            ON mt.placement_id = sp.placement_id
        LEFT JOIN attribution a
            ON a.touch_id = mt.touch_id
        GROUP BY
            sp.campaign_id,
            sc.name,
            sp.placement_id,
            sp.channel_name,
            sp.creative_id,
            sp.cost
        ORDER BY revenue DESC
        """
    ).fetchall()

    result = []

    for row in rows:
        item = dict(row)

        cost = item["cost"] or 0
        revenue = item["revenue"] or 0

        item["romi"] = (
            ((revenue - cost) / cost) * 100
            if cost > 0
            else 0
        )

        result.append(item)

    connection.close()

    return result

@app.get("/analytics/sales/courses")
def sales_by_courses():
    df = pd.read_excel(
        BASE_XLSX_PATH,
        sheet_name="Данные",
        usecols=["Номер студента", "Сумма", "Курс"],
    )

    df = df.rename(columns={
        "Номер студента": "student_id",
        "Сумма": "amount",
        "Курс": "course",
    })

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce",
    ).fillna(0)

    result = (
        df.groupby("course", as_index=False)
        .agg(
            purchases=("course", "size"),
            customers=("student_id", "nunique"),
            revenue=("amount", "sum"),
            average_check=("amount", "mean"),
        )
        .sort_values("revenue", ascending=False)
    )

    result["revenue"] = result["revenue"].round(2)
    result["average_check"] = result["average_check"].round(2)

    return result.to_dict(orient="records")


@app.get("/analytics/sales/daily")
def sales_by_day():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            DATE(purchased_at) AS date,
            COUNT(*) AS purchases,
            SUM(amount) AS revenue
        FROM sales
        GROUP BY DATE(purchased_at)
        ORDER BY date
        """
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]

@app.get("/analytics/sales/customers")
def customer_analytics():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            student_id,
            COUNT(*) AS purchases,
            SUM(amount) AS revenue,
            MIN(purchased_at) AS first_purchase,
            MAX(purchased_at) AS last_purchase
        FROM sales
        GROUP BY student_id
        ORDER BY revenue DESC
        """
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]

@app.get("/analytics/funnel")
def analytics_funnel():
    connection = get_connection()

    clicks = connection.execute(
        """
        SELECT COUNT(*)
        FROM marketing_touches
        WHERE event_type = 'click'
        """
    ).fetchone()[0]

    bot_starts = connection.execute(
        """
        SELECT COUNT(*)
        FROM marketing_touches
        WHERE event_type = 'bot_start'
        """
    ).fetchone()[0]

    leads = connection.execute(
        """
        SELECT COUNT(*)
        FROM marketing_touches
        WHERE event_type = 'lead'
        """
    ).fetchone()[0]

    buyers = connection.execute(
        """
        SELECT COUNT(DISTINCT student_id)
        FROM attribution
        """
    ).fetchone()[0]

    revenue = connection.execute(
        """
        SELECT COALESCE(SUM(attributed_revenue), 0)
        FROM attribution
        """
    ).fetchone()[0]

    connection.close()

    return {
        "clicks": clicks,
        "bot_starts": bot_starts,
        "leads": leads,
        "buyers": buyers,
        "revenue": revenue,
    }

@app.get("/analytics/attribution/{student_id}")
def analytics_student_attribution(student_id: str):
    connection = get_connection()

    touches = connection.execute(
        """
        SELECT
    touch_id,
    campaign_id,
    placement_id,
    creative_id,
    tracking_id,
    event_type,
    touched_at
FROM marketing_touches
        WHERE student_id = ?
        ORDER BY touched_at
        """,
        (student_id,)
    ).fetchall()

    purchases = connection.execute(
        """
        SELECT
            sale_id,
            course,
            amount,
            purchased_at
        FROM sales
        WHERE student_id = ?
        ORDER BY purchased_at
        """,
        (student_id,)
    ).fetchall()

    total_revenue = connection.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM sales
        WHERE student_id = ?
        """,
        (student_id,)
    ).fetchone()[0]

    connection.close()

    return {
        "student_id": student_id,
        "touches": [dict(row) for row in touches],
        "purchases": [dict(row) for row in purchases],
        "total_revenue": total_revenue,
    }
