from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from aiogram.types import User as TgUser


@dataclass
class NutritionPer100g:
    kcal: Optional[float]
    protein: Optional[float]
    fat: Optional[float]
    carbs: Optional[float]


@dataclass
class NutritionPerServing:
    size: Optional[str]
    kcal: Optional[float]
    protein: Optional[float]
    fat: Optional[float]
    carbs: Optional[float]


@dataclass
class NutritionResponse:
    barcode: str
    name: str
    per_100g: NutritionPer100g
    serving: NutritionPerServing


@dataclass
class DailyStats:
    date: str
    kcal: float
    protein: float
    fat: float
    carbs: float


@dataclass
class TrackBarcodeResponse:
    barcode: str
    name: str
    amount_grams: Optional[float]
    servings: Optional[float]
    per_100g: NutritionPer100g
    serving: NutritionPerServing
    daily: DailyStats


@dataclass
class UserProfile:
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]


@dataclass
class UserMeResponse:
    profile: UserProfile
    today: Optional[DailyStats]


class KBJUApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(method, url, json=json, params=params)
        return resp

    # ---------- Мапперы ----------

    @staticmethod
    def _nutrition_per_100g_from_dict(data: Dict[str, Any]) -> NutritionPer100g:
        return NutritionPer100g(
            kcal=data.get("kcal"),
            protein=data.get("protein"),
            fat=data.get("fat"),
            carbs=data.get("carbs"),
        )

    @staticmethod
    def _nutrition_per_serving_from_dict(data: Dict[str, Any]) -> NutritionPerServing:
        return NutritionPerServing(
            size=data.get("size"),
            kcal=data.get("kcal"),
            protein=data.get("protein"),
            fat=data.get("fat"),
            carbs=data.get("carbs"),
        )

    @staticmethod
    def _daily_from_dict(data: Dict[str, Any]) -> DailyStats:
        return DailyStats(
            date=data["date"],
            kcal=data["kcal"],
            protein=data["protein"],
            fat=data["fat"],
            carbs=data["carbs"],
        )

    # ---------- Публичные методы ----------

    async def get_bju_by_barcode(self, barcode: str) -> Optional[NutritionResponse]:
        resp = await self._request("GET", f"/barcode/{barcode}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()

        return NutritionResponse(
            barcode=data["barcode"],
            name=data["name"],
            per_100g=self._nutrition_per_100g_from_dict(data["per_100g"]),
            serving=self._nutrition_per_serving_from_dict(data["serving"]),
        )

    async def track_bju_by_barcode(
        self,
        barcode: str,
        tg_user: TgUser,
        grams: Optional[float] = None,
        servings: Optional[float] = None,
    ) -> TrackBarcodeResponse:
        payload: Dict[str, Any] = {
            "telegram_user": self._telegram_user_payload(tg_user),
            "grams": grams,
            "servings": servings,
        }

        resp = await self._request("POST", f"/barcode/{barcode}/track", json=payload)
        resp.raise_for_status()
        data = resp.json()

        return TrackBarcodeResponse(
            barcode=data["barcode"],
            name=data["name"],
            amount_grams=data["amount_grams"],
            servings=data["servings"],
            per_100g=self._nutrition_per_100g_from_dict(data["per_100g"]),
            serving=self._nutrition_per_serving_from_dict(data["serving"]),
            daily=self._daily_from_dict(data["daily"]),
        )

    async def get_me(self, telegram_id: int) -> Optional[UserMeResponse]:
        resp = await self._request(
            "GET",
            "/users/me",
            params={"telegram_id": telegram_id},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()

        profile_data = data["profile"]
        today_data = data.get("today")

        profile = UserProfile(
            id=profile_data["id"],
            telegram_id=profile_data["telegram_id"],
            username=profile_data.get("username"),
            first_name=profile_data.get("first_name"),
            last_name=profile_data.get("last_name"),
        )
        today = self._daily_from_dict(today_data) if today_data else None

        return UserMeResponse(profile=profile, today=today)

    @staticmethod
    def _telegram_user_payload(tg_user: TgUser) -> Dict[str, Any]:
        return {
            "id": tg_user.id,
            "is_bot": tg_user.is_bot,
            "first_name": tg_user.first_name,
            "last_name": tg_user.last_name,
            "username": tg_user.username,
            "language_code": getattr(tg_user, "language_code", None),
            "is_premium": getattr(tg_user, "is_premium", None),
        }
