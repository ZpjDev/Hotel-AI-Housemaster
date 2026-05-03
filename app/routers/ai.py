from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database import get_session
from app.schemas import (
    StrategyRequest, StrategyResponse, SuggestedPriceItem, ActionRequiredItem,
    MonthlyReportRequest, MonthlyReportResponse,
)
from app.services.ai_provider import AIProvider
from app.services.strategy_service import StrategyService
from app.services.external_api.ota_data_service import OTADataService
from app.services.report_service import ReportService
from app.services.crud_strategy import create_strategy_report
from app.models import StrategyReport
from datetime import datetime
import json

router = APIRouter()


@router.post("/ai/strategy", response_model=StrategyResponse)
async def api_generate_strategy(
    request: StrategyRequest,
    session: Session = Depends(get_session),
):
    """生成 AI 经营策略"""
    ai = AIProvider()
    ota = OTADataService(session)
    strategy_svc = StrategyService(session, ai, ota)

    try:
        result = await strategy_svc.generate_strategy(
            hotel_id=request.hotel_id,
            target_date=request.target_date,
            time_slot=request.time_slot,
            question=request.question,
        )

        sp_json = json.dumps(result.get("suggested_prices", []), ensure_ascii=False)
        ar_json = json.dumps(result.get("actions_required", []), ensure_ascii=False)

        report = StrategyReport(
            hotel_id=request.hotel_id,
            date=result["date"],
            time_slot=result["time_slot"],
            question=request.question,
            market_analysis=result["market_analysis"],
            competitor_analysis=result["competitor_analysis"],
            suggested_price=result["suggested_price"],
            suggested_prices_json=sp_json,
            room_control_strategy=result["room_control_strategy"],
            ota_strategy=result["ota_strategy"],
            promotion_strategy=result["promotion_strategy"],
            direct_customer_strategy=result["direct_customer_strategy"],
            risk_alert=result["risk_alert"],
            actions_required_json=ar_json,
            full_report=result["full_report"],
            created_at=datetime.now(),
        )
        create_strategy_report(session, report)

        return StrategyResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略生成失败: {str(e)}")


@router.post("/reports/monthly", response_model=MonthlyReportResponse)
async def api_monthly_report(
    request: MonthlyReportRequest,
    session: Session = Depends(get_session),
):
    """生成月度经营报告"""
    ai = AIProvider()
    report_svc = ReportService(session, ai)
    report = await report_svc.generate_monthly_report(request.hotel_id, request.month)
    return MonthlyReportResponse(hotel_id=request.hotel_id, month=request.month, report=report)


@router.post("/reviews/{review_id}/reply")
async def api_reply_review(
    review_id: int,
    session: Session = Depends(get_session),
):
    """生成点评回复"""
    from app.models import Review
    from app.services.crud_others import update_review_reply

    review = session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="点评不存在")

    ai = AIProvider()

    rating_prompt = {
        5: "客人给出了满分好评。请感谢客人的认可，强化入住亮点，并邀请再次光临。",
        4: "客人给出了 4 分好评。请感谢客人，提及做得好的地方，并表达持续改进的意愿。",
        3: "客人给出了 3 分中评。请感谢反馈，解释可能的问题，承诺改进，邀请再次体验。",
        2: "客人给出了 2 分差评。请先道歉，具体回应问题，提出补救措施，邀请私聊沟通。",
        1: "客人给出了 1 分差评。请诚恳道歉，认真对待每个问题，给出具体解决方案，邀请进一步沟通。",
    }

    prompt = f"""客人评价（{review.rating}分）：
{review.content}

{rating_prompt.get(review.rating, "请根据评价内容生成合适的回复。")}

要求：
- 语气真诚、专业
- 不与客户争论
- 不承诺无法兑现的补偿
- 回复控制在 100 字以内
"""

    try:
        reply = await ai.chat_completion([
            {"role": "system", "content": "你是一位专业的酒店客服经理，擅长处理客户点评回复。"},
            {"role": "user", "content": prompt},
        ])
    except Exception:
        if review.rating >= 4:
            reply = "感谢您的认可与支持！很高兴您度过愉快的入住体验，期待您的再次光临。我们会继续努力为您提供更好的服务！"
        elif review.rating == 3:
            reply = "感谢您的反馈。对于您提到的问题，我们已记录并会持续改进。期待下次入住能给您带来更好的体验！"
        else:
            reply = "非常抱歉给您带来不好的体验。我们已收到您的反馈，会认真改进。如有需要，请随时联系我们，我们将全力协助。"

    update_review_reply(session, review_id, reply)

    return {"review_id": review_id, "reply": reply}
