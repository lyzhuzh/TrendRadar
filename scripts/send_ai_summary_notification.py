# coding=utf-8
"""
发送 AI 总结通知脚本
用于 GitHub Actions 工作流中发送 AI 生成的每日摘要
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trendradar.core import load_config
from trendradar.context import AppContext
from trendradar.notification.dispatcher import NotificationDispatcher


def send_ai_notification(summary_file: str) -> bool:
    """
    发送 AI 总结通知

    Args:
        summary_file: AI 总结文件路径

    Returns:
        bool: 是否发送成功
    """
    if not Path(summary_file).exists():
        print(f"[ERROR] Summary file not found: {summary_file}")
        return False

    # 读取总结内容
    with open(summary_file, "r", encoding="utf-8") as f:
        summary_content = f.read()

    # 加载配置
    config = load_config()
    notification_config = config.get("NOTIFICATION", {})

    # 检查是否配置了通知渠道
    has_any_channel = any([
        notification_config.get("FEISHU_WEBHOOK_URL"),
        notification_config.get("DINGTALK_WEBHOOK_URL"),
        notification_config.get("TELEGRAM_BOT_TOKEN") and notification_config.get("TELEGRAM_CHAT_ID"),
        notification_config.get("WEWORK_WEBHOOK_URL"),
        notification_config.get("EMAIL_TO"),
        notification_config.get("NTFY_SERVER_URL"),
        notification_config.get("BARK_URL"),
        notification_config.get("SLACK_WEBHOOK_URL"),
    ])

    if not has_any_channel:
        print("[WARNING] No notification channels configured")
        return False

    # 创建 AppContext 和调度器
    ctx = AppContext(config)
    dispatcher = ctx.create_notification_dispatcher()

    # 准备空报告数据（AI 总结不需要其他数据）
    report_data = {
        "date": ctx.format_date(),
        "time": ctx.format_time(),
        "stats": {},
        "keywords": [],
        "platforms": [],
    }

    # 发送通知（只发送 AI 总结）
    results = dispatcher.dispatch_all(
        report_data=report_data,
        report_type="AI每日摘要",
        mode="daily",
        ai_summary=summary_content,
    )

    # 检查结果
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"[OK] Sent to {success_count}/{total_count} channels")

    if success_count == 0:
        print("[ERROR] All notification channels failed")
        return False

    return True


if __name__ == "__main__":
    # 从命令行参数或环境变量获取摘要文件
    if len(sys.argv) > 1:
        summary_file = sys.argv[1]
    else:
        # 默认使用最新的摘要文件
        summary_dir = Path("output/ai_summaries")
        if not summary_dir.exists():
            print("[ERROR] AI summaries directory not found")
            sys.exit(1)

        summary_files = sorted(summary_dir.glob("summary_*.md"), reverse=True)
        if not summary_files:
            print("[ERROR] No summary files found")
            sys.exit(1)

        summary_file = str(summary_files[0])

    print(f"Sending AI summary notification: {summary_file}")

    if send_ai_notification(summary_file):
        print("[OK] AI summary notification sent successfully")
        sys.exit(0)
    else:
        print("[ERROR] Failed to send AI summary notification")
        sys.exit(1)
