# -*- coding: utf-8 -*-
import datetime
import requests
from jqdatasdk import *

# ====================== 替换成你的配置 ======================
JQ_USER = "17740525736"
JQ_PWD = "Qq@81935608"
SEND_KEY = "SCT327806TOF5XXN0QFBHB3idhwKkqeecw"  # 带引号！
# ====================== 策略参数 ======================
AVG_DAYS = 5          # 5日均价
MAX_HOLD = 3          # 最大持仓3只
MAX_POS_RATIO = 0.8   # 持仓占比≤80%
STOCK_POOL = ['600026.XSHG', '000856.XSHE', '300014.XSHE']

# 微信通知函数
def send_wechat(title, content):
    if not SEND_KEY:
        print("SendKey未配置，跳过通知")
        return
    url = f"https://sctapi.ftqq.com/{SEND_KEY}.send"
    data = {"title": title, "desp": content.replace("\n", "\n\n")}
    try:
        requests.post(url, data=data, timeout=10, verify=False)
        print("微信通知发送成功")
    except Exception as e:
        print(f"微信通知发送失败：{str(e)}")

# 核心策略逻辑
def run_strategy():
    # 1. 登录聚宽（非会员也能获取基础日线数据）
    try:
        auth(JQ_USER, JQ_PWD)
        print("聚宽登录成功")
    except Exception as e:
        send_wechat("【策略错误】聚宽登录失败", f"错误原因：{str(e)}")
        return

    # 2. 周末休市不运行
    today = datetime.date.today()
    if today.weekday() >= 5:
        print(f"今日{today}是周末，休市不运行")
        return

    # 3. 模拟账户数据（非会员无法对接实盘/模拟盘，仅模拟计算）
    total_asset = 100000.0  # 初始资金10万
    hold_stocks = []         # 模拟持仓
    hold_value = 0.0         # 模拟持仓市值

    # 4. 卖出逻辑：价格 > 5日均价
    sell_msgs = []
    for stock in hold_stocks.copy():
        # 获取5日均价
        try:
            df = get_price(
                stock,
                end_date=today,
                count=AVG_DAYS,
                frequency='daily',
                fields=['close']
            )
            if len(df) < AVG_DAYS:
                print(f"{stock}数据不足{AVG_DAYS}天，跳过卖出")
                continue
            ma5 = round(df['close'].mean(), 2)
            current_price = round(df['close'].iloc[-1], 2)

            # 卖出条件
            if current_price > ma5:
                sell_msg = f"📤 卖出 {stock}\n当前价：{current_price} 元\n5日均价：{ma5} 元"
                sell_msgs.append(sell_msg)
                hold_stocks.remove(stock)
                print(sell_msg)
        except Exception as e:
            print(f"{stock}卖出逻辑异常：{str(e)}")

    # 发送卖出通知
    if sell_msgs:
        send_wechat(f"【策略卖出通知】{today}", "\n\n".join(sell_msgs))

    # 5. 买入逻辑：价格 < 5日均价
    can_buy_num = MAX_HOLD - len(hold_stocks)
    if can_buy_num <= 0:
        print("持仓已达3只上限，跳过买入")
        return

    # 计算可买入资金
    max_pos_value = round(total_asset * MAX_POS_RATIO, 2)
    available_cash = round(min(total_asset - hold_value, max_pos_value - hold_value), 2)
    if available_cash <= 0:
        print("无可用资金/持仓已达80%上限，跳过买入")
        return
    per_stock_cash = round(available_cash / can_buy_num, 2)

    # 筛选买入标的
    buy_candidates = []
    for stock in STOCK_POOL:
        if stock in hold_stocks:
            continue
        try:
            df = get_price(
                stock,
                end_date=today,
                count=AVG_DAYS,
                frequency='daily',
                fields=['close']
            )
            if len(df) < AVG_DAYS:
                print(f"{stock}数据不足{AVG_DAYS}天，跳过买入")
                continue
            ma5 = round(df['close'].mean(), 2)
            current_price = round(df['close'].iloc[-1], 2)

            if current_price < ma5 and current_price > 0:
                buy_candidates.append((stock, current_price, ma5))
        except Exception as e:
            print(f"{stock}买入逻辑异常：{str(e)}")

    # 执行买入（模拟）
    buy_msgs = []
    for stock, price, ma5 in buy_candidates[:can_buy_num]:
        buy_amount = int(per_stock_cash / price / 100) * 100
        if buy_amount > 0:
            buy_msg = f"📥 买入 {stock}\n当前价：{price} 元\n5日均价：{ma5} 元\n数量：{buy_amount} 股"
            buy_msgs.append(buy_msg)
            hold_stocks.append(stock)
            print(buy_msg)

    # 发送买入通知
    if buy_msgs:
        send_wechat(f"【策略买入通知】{today}", "\n\n".join(buy_msgs))

    print(f"策略运行完成 | 当日持仓：{hold_stocks}")

if __name__ == "__main__":
    run_strategy()
