import os
import smtplib
import ssl
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. 调度逻辑：判断今天应发送哪种报告 ---
def get_report_type():
    """根据今天的日期判断需要生成的报告类型"""
    today = date.today()
    
    # 周六：政策与费用周报
    if today.weekday() == 5:
        return "政策与费用周报", "请总结本周亚马逊平台在政策、费用结构、卖家工具及合规要求方面的主要变化与更新。"

    # 双周日：市场与卖家生态双周报 (基准日 2026-03-15)
    baseline = date(2026, 3, 15)
    if today.weekday() == 6 and (today - baseline).days % 14 == 0:
        return "市场与卖家生态双周报", "请分析过去两周亚马逊主要目标市场的宏观趋势、消费者行为变化、新兴品类机会，以及卖家生态（如新卖家数量、头部卖家动态、服务商工具创新等）的关键动态。"

    # 季度首月5日：财报与技术创新季报
    if today.month in [1, 4, 7, 10] and today.day == 5:
        return "财报与技术创新季报", "请结合亚马逊最新发布的财报，深入解读其电商、AWS、广告等核心业务的表现。同时，全面梳理并分析其在人工智能、物流、自动化、云计算等领域披露的最新技术创新、专利申请及未来研发布局。"

    return None, None

# --- 2. 内容生成：调用 LLM API ---
def generate_report_content(report_title, prompt):
    """调用大语言模型 API 生成报告内容"""
    print(f"正在生成报告: {report_title}")
    
    # 此处为调用 LLM 的伪代码，您需要根据选择的平台（OpenAI/Claude）替换为实际的 API 调用
    # 您需要从 GitHub Secrets 获取 API Key
    # llm_api_key = os.environ.get("LLM_API_KEY")
    
    # 示例：
    # response = requests.post(
    #     "LLM_API_ENDPOINT",
    #     headers={"Authorization": f"Bearer {llm_api_key}"},
    #     json={"model": "chosen_model", "messages": [{"role": "user", "content": prompt}]}
    # )
    # report_content = response.json()["choices"][0]["message"]["content"]
    
    # 为演示，此处返回一个占位符文本
    report_content = f"这是关于《{report_title}》的详细报告内容。\n\n{prompt}"
    
    print("报告内容生成完毕。")
    return report_content

# --- 3. 邮件发送：使用 Gmail SMTP ---
def send_email(report_title, report_content):
    """将生成的报告通过 Gmail 发送"""
    sender_email = os.environ.get("GMAIL_USER")
    receiver_email = os.environ.get("RECIPIENT_EMAIL")
    password = os.environ.get("GMAIL_APP_PASSWORD")

    if not all([sender_email, receiver_email, password]):
        print("邮件配置信息不完整，无法发送。")
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = f"亚马逊动态推送 | {report_title} ({date.today().strftime("%Y-%m-%d")})"
    message["From"] = sender_email
    message["To"] = receiver_email

    # 创建邮件正文 (HTML 格式，更美观)
    html = f"""
    <html>
      <body>
        <h1>{report_title}</h1>
        <p>报告生成日期: {date.today().strftime("%Y-%m-%d")}</p>
        <hr>
        <pre style="white-space: pre-wrap; font-family: sans-serif;">{report_content}</pre>
      </body>
    </html>
    """
    message.attach(MIMEText(html, "html"))

    try:
        print(f"正在发送邮件至 {receiver_email}...")
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("邮件发送成功！")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False

# --- 主函数 ---
if __name__ == "__main__":
    report_title, prompt = get_report_type()
    
    if report_title:
        print(f"任务触发：今天需发送《{report_title}》")
        content = generate_report_content(report_title, prompt)
        send_email(report_title, content)
    else:
        print(f"任务跳过：今天 ({date.today().strftime("%Y-%m-%d")}) 无需发送报告。")
