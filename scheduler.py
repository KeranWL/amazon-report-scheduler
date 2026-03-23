import os
import smtplib
import ssl
import json
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openai import OpenAI
import requests
from bs4 import BeautifulSoup

# --- 1. 调度逻辑 ---
def get_report_type():
    today = date.today()

    if today.weekday() == 5:
        return "政策与费用周报", "请总结本周亚马逊平台在政策、费用结构、卖家工具及合规要求方面的主要变化与更新。"

    baseline = date(2026, 3, 15)
    if today.weekday() == 6 and (today - baseline).days % 14 == 0:
        return "市场与卖家生态双周报", "请分析过去两周亚马逊市场趋势、消费者行为变化及卖家生态动态。"

    if today.month in [1, 4, 7, 10] and today.day == 5:
        return "财报与技术创新季报", "请结合亚马逊财报，分析业务表现与技术创新方向。"

    return None, None


# --- 2. 读取信源配置 ---
def load_sources():
    with open("sources.json", "r", encoding="utf-8") as f:
        return json.load(f)


# --- 3. 生成报告（OpenAI + 信源控制） ---
def generate_report_content(report_title, prompt):
    print(f"正在生成报告: {report_title}")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise Exception("缺少 OPENAI_API_KEY")

    client = OpenAI(api_key=api_key)

    # 读取信源
    sources = load_sources()

    core_sources = "\n".join([f"- {s['name']}: {s['url']}" for s in sources["core_sources"]])
    industry_sources = "\n".join([f"- {s['name']}: {s['url']}" for s in sources["industry_sources"]])
    ai_topics = "\n".join([f"- {t}" for t in sources["ai_search_topics"]])

    # 构建 Prompt（核心升级点）
    full_prompt = f"""
你是一名资深亚马逊美国站运营分析师。

请基于以下信源进行信息整合：

【核心信源（最高优先级）】
{core_sources}

【行业信源】
{industry_sources}

【补充搜索方向】
{ai_topics}

任务：
生成《{report_title}》

要求（必须严格遵守）：
- 只输出最重要的 2-3 条信息
- 每条信息结构如下：
  1️⃣ 发生了什么（1句话）
  2️⃣ 影响（1句话）
  3️⃣ 动作（1句话）

- 不要长分析
- 不要背景介绍
- 不要废话

内容范围：
{prompt}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.3
    )

    content = response.choices[0].message.content
    print("报告生成完成")
    return content


# --- 4. 邮件发送 ---
def send_email(report_title, report_content):
    sender_email = os.environ.get("EMAIL_USER")
    receiver_email = os.environ.get("EMAIL_TO")
    password = os.environ.get("EMAIL_PASS")

    if not all([sender_email, receiver_email, password]):
        print("邮件配置缺失")
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = f"亚马逊动态推送 | {report_title} ({date.today().strftime('%Y-%m-%d')})"
    message["From"] = sender_email
    message["To"] = receiver_email

    html = f"""
    <html>
      <body>
        <h2>{report_title}</h2>
        <p>日期：{date.today().strftime('%Y-%m-%d')}</p>
        <hr>
        <pre style="white-space: pre-wrap; font-size:14px;">{report_content}</pre>
      </body>
    </html>
    """

    message.attach(MIMEText(html, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("邮件发送成功")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False


# --- 主执行 ---
if __name__ == "__main__":
    report_title, prompt = get_report_type()

    if report_title:
        print(f"执行任务：{report_title}")
        content = generate_report_content(report_title, prompt)
        send_email(report_title, content)
    else:
        print(f"今日无需发送 ({date.today().strftime('%Y-%m-%d')})")
