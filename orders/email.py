"""
orders/email.py
─────────────────────────────────────────────────────────────────────────────
Email notification helpers for the orders app.

In development the Django console email backend prints to stdout.
In production set EMAIL_BACKEND to an SMTP backend in settings/.env.
"""

import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)


def send_order_confirmation(order) -> bool:
    """
    Send a plain-text + HTML order confirmation email to the customer.
    Returns True if the mail was sent, False if it silently failed.
    Failures are logged as warnings so they never crash the request.
    """
    subject   = f'Order Confirmed – Lakshmi Crackers (Order #{order.id})'
    from_addr = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lakshmicrackers.com')

    # ── Build item lines ───────────────────────────────────────────────────────
    item_lines_txt  = '\n'.join(
        f'  • {item.product_name} × {item.quantity}  →  ₹{float(item.line_total):.0f}'
        for item in order.items.all()
    )
    item_lines_html = ''.join(
        f'<tr>'
        f'<td style="padding:6px 12px;border-bottom:1px solid #fde68a;">{item.product_name}</td>'
        f'<td style="padding:6px 12px;border-bottom:1px solid #fde68a;text-align:center;">{item.quantity}</td>'
        f'<td style="padding:6px 12px;border-bottom:1px solid #fde68a;text-align:right;">₹{float(item.line_total):.0f}</td>'
        f'</tr>'
        for item in order.items.all()
    )

    discount_line_txt  = (
        f'\n  Coupon ({order.coupon_code}): - ₹{float(order.discount_amount):.0f}'
        if order.discount_amount else ''
    )
    discount_line_html = (
        f'<tr><td colspan="2" style="padding:4px 12px;color:#16a34a;">Discount ({order.coupon_code})</td>'
        f'<td style="padding:4px 12px;color:#16a34a;text-align:right;">- ₹{float(order.discount_amount):.0f}</td></tr>'
        if order.discount_amount else ''
    )

    # ── Plain-text body ────────────────────────────────────────────────────────
    plain_body = f"""
Dear {order.name},

Thank you for shopping with Lakshmi Crackers! 🪔

Your order has been received and our team will contact you at {order.phone}
within 24 hours to confirm payment.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ORDER DETAILS  (#{order.id})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{item_lines_txt}
{discount_line_txt}
  ─────────────────────────────────
  Total Payable:  ₹{float(order.total):.0f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Delivery Address:
{order.address}

Payment will be collected via UPI / bank transfer / cash on delivery
after our team contacts you.

Happy Diwali! 🎆
— Team Lakshmi Crackers
  📞 +91 63748 01083  |  ✉ lakshmicrackersonline@gmail.com
    """.strip()

    # ── HTML body ──────────────────────────────────────────────────────────────
    html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#fef3c7;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#fef3c7;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08);">

        <!-- Header -->
        <tr>
          <td style="background:#b91c1c;padding:28px 32px;text-align:center;">
            <p style="margin:0;font-size:32px;">🪔</p>
            <h1 style="margin:8px 0 4px;color:#fde68a;font-size:22px;letter-spacing:1px;">
              LAKSHMI CRACKERS
            </h1>
            <p style="margin:0;color:#fca5a5;font-size:13px;">Order Confirmation</p>
          </td>
        </tr>

        <!-- Greeting -->
        <tr>
          <td style="padding:28px 32px 16px;">
            <h2 style="margin:0 0 8px;color:#1f2937;font-size:20px;">
              Thank you, {order.name}! 🎉
            </h2>
            <p style="margin:0;color:#6b7280;font-size:14px;line-height:1.6;">
              Your order <strong style="color:#b91c1c;">#{order.id}</strong> has been received.
              Our team will call you at <strong>{order.phone}</strong> within 24 hours
              to confirm payment.
            </p>
          </td>
        </tr>

        <!-- Items table -->
        <tr>
          <td style="padding:0 32px 24px;">
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="border-collapse:collapse;border:1px solid #fde68a;border-radius:8px;overflow:hidden;">
              <thead>
                <tr style="background:#fef3c7;">
                  <th style="padding:10px 12px;text-align:left;font-size:12px;color:#92400e;
                             text-transform:uppercase;letter-spacing:.5px;">Product</th>
                  <th style="padding:10px 12px;text-align:center;font-size:12px;color:#92400e;
                             text-transform:uppercase;letter-spacing:.5px;">Qty</th>
                  <th style="padding:10px 12px;text-align:right;font-size:12px;color:#92400e;
                             text-transform:uppercase;letter-spacing:.5px;">Amount</th>
                </tr>
              </thead>
              <tbody>
                {item_lines_html}
                {discount_line_html}
                <tr style="background:#fef3c7;">
                  <td colspan="2"
                      style="padding:12px;font-weight:bold;font-size:15px;color:#1f2937;">
                    Total Payable
                  </td>
                  <td style="padding:12px;font-weight:bold;font-size:18px;
                             color:#b91c1c;text-align:right;">
                    ₹{float(order.total):.0f}
                  </td>
                </tr>
              </tbody>
            </table>
          </td>
        </tr>

        <!-- Address -->
        <tr>
          <td style="padding:0 32px 24px;">
            <div style="background:#f9fafb;border-left:4px solid #b91c1c;
                        border-radius:4px;padding:14px 16px;">
              <p style="margin:0 0 4px;font-size:12px;color:#9ca3af;
                        text-transform:uppercase;letter-spacing:.5px;">Delivery Address</p>
              <p style="margin:0;font-size:14px;color:#374151;line-height:1.5;">
                {order.address}
              </p>
            </div>
          </td>
        </tr>

        <!-- Payment note -->
        <tr>
          <td style="padding:0 32px 28px;">
            <div style="background:#fffbeb;border:1px solid #fde68a;
                        border-radius:8px;padding:16px;text-align:center;">
              <p style="margin:0;font-size:13px;color:#92400e;line-height:1.6;">
                📞 <strong>Payment Confirmation</strong><br>
                Our team will contact you via phone/WhatsApp to collect payment
                through UPI, bank transfer, or cash on delivery.
              </p>
            </div>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#b91c1c;padding:20px 32px;text-align:center;">
            <p style="margin:0;color:#fde68a;font-size:16px;font-weight:bold;">
              Happy Diwali! 🎆
            </p>
            <p style="margin:6px 0 0;color:#fca5a5;font-size:12px;">
              📞 +91 63748 01083 &nbsp;|&nbsp; ✉ lakshmicrackersonline@gmail.com
            </p>
            <p style="margin:8px 0 0;color:#fca5a5;font-size:11px;">
              4/214, Near Enammeenatchipuram Bus Stop, Vembakottai, Sivakasi, TN - 626131
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
    """.strip()

    try:
        msg = EmailMultiAlternatives(subject, plain_body, from_addr, [order.email])
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        logger.info('Order confirmation email sent to %s for order #%s', order.email, order.id)
        return True
    except Exception as exc:
        logger.warning(
            'Failed to send confirmation email for order #%s to %s: %s',
            order.id, order.email, exc
        )
        return False


def send_order_status_update(order) -> bool:
    """
    Notify the customer when their order status changes (e.g. shipped).
    """
    STATUS_MESSAGES = {
        'confirmed':  ('Your order has been confirmed! 🎉', 'We\'re preparing your crackers.'),
        'processing': ('Your order is being processed! 📦', 'Our team is packing your items.'),
        'shipped':    ('Your order is on its way! 🚚', 'Expect delivery within 2–3 business days.'),
        'delivered':  ('Your order has been delivered! 🎆', 'Enjoy your celebration!'),
        'cancelled':  ('Your order has been cancelled.', 'Contact us if you have any questions.'),
    }

    status_info = STATUS_MESSAGES.get(order.status)
    if not status_info:
        return False

    headline, subtext = status_info
    subject   = f'Order #{order.id} Update – {headline}'
    from_addr = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lakshmicrackers.com')

    plain_body = (
        f'Dear {order.name},\n\n'
        f'{headline}\n{subtext}\n\n'
        f'Order ID: #{order.id}\n'
        f'Current Status: {order.status.title()}\n\n'
        f'— Team Lakshmi Crackers'
    )

    try:
        send_mail(subject, plain_body, from_addr, [order.email], fail_silently=False)
        logger.info('Status update email sent for order #%s (%s)', order.id, order.status)
        return True
    except Exception as exc:
        logger.warning('Failed to send status email for order #%s: %s', order.id, exc)
        return False


def send_admin_order_notification(order) -> bool:
    """
    Send an instant notification to the shop owner (lakshmicrackersonline@gmail.com)
    every time a new order is placed.
    Never crashes the request — failures are logged silently.
    """
    ADMIN_EMAIL = 'lakshmicrackersonline@gmail.com'
    from_addr   = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lakshmicrackers.com')
    subject     = f'[NEW ORDER] #{order.id} — Rs.{float(order.total):.0f} from {order.name}'

    # Build item lines
    item_lines_txt = '\n'.join(
        f'  {i+1}. {item.product_name} x{item.quantity}  =  Rs.{float(item.line_total):.0f}'
        for i, item in enumerate(order.items.all())
    )
    item_lines_html = ''.join(
        f'<tr style="background:{"#f9fafb" if i%2==0 else "#fff"}">'
        f'<td style="padding:7px 12px;border-bottom:1px solid #e5e7eb;font-size:13px">{item.product_name}</td>'
        f'<td style="padding:7px 12px;border-bottom:1px solid #e5e7eb;text-align:center;font-size:13px;font-weight:700">x{item.quantity}</td>'
        f'<td style="padding:7px 12px;border-bottom:1px solid #e5e7eb;text-align:right;font-size:13px;font-weight:700">Rs.{float(item.line_total):.0f}</td>'
        f'</tr>'
        for i, item in enumerate(order.items.all())
    )

    discount_txt  = (
        f'\n  Discount ({order.coupon_code}): - Rs.{float(order.discount_amount):.0f}'
        if order.discount_amount else ''
    )
    discount_html = (
        f'<tr><td colspan="2" style="padding:6px 12px;font-size:12px;color:#15803d">Discount ({order.coupon_code})</td>'
        f'<td style="padding:6px 12px;font-size:12px;color:#15803d;text-align:right">- Rs.{float(order.discount_amount):.0f}</td></tr>'
        if order.discount_amount else ''
    )

    import datetime
    order_time = order.created_at.strftime('%d %b %Y, %I:%M %p') if order.created_at else 'N/A'

    plain_body = f"""
NEW ORDER RECEIVED — Lakshmi Crackers
======================================
Order ID   : #{order.id}
Time       : {order_time}
--------------------------------------
CUSTOMER
  Name   : {order.name}
  Phone  : {order.phone}
  Email  : {order.email or 'Not provided'}
--------------------------------------
DELIVERY ADDRESS
  {order.address}
--------------------------------------
ITEMS
{item_lines_txt}{discount_txt}
--------------------------------------
  TOTAL  : Rs.{float(order.total):.0f}
======================================
Login to admin: https://www.lakshmicrackers.com/admin/orders
""".strip()

    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="padding:24px 16px;background:#f3f4f6">
<tr><td align="center">
<table width="580" cellpadding="0" cellspacing="0"
       style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)">

  <!-- Alert Header -->
  <tr>
    <td style="background:#1f2937;padding:20px 28px;display:flex;justify-content:space-between;align-items:center">
      <table width="100%"><tr>
        <td>
          <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">New Order Received</div>
          <div style="font-size:22px;font-weight:700;color:#fff">Order #{order.id}</div>
          <div style="font-size:12px;color:#9ca3af;margin-top:4px">{order_time}</div>
        </td>
        <td style="text-align:right">
          <div style="background:#16a34a;color:#fff;padding:6px 16px;border-radius:20px;
                      font-size:12px;font-weight:700;display:inline-block">
            Rs.{float(order.total):.0f}
          </div>
        </td>
      </tr></table>
    </td>
  </tr>

  <!-- Customer Info -->
  <tr>
    <td style="padding:20px 28px 0">
      <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;
                  color:#6b7280;border-bottom:1px solid #e5e7eb;padding-bottom:6px;margin-bottom:12px">
        Customer Details
      </div>
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="width:50%;vertical-align:top;padding-right:16px">
            <div style="font-size:11px;color:#9ca3af;margin-bottom:2px">Name</div>
            <div style="font-size:14px;font-weight:700;color:#111;margin-bottom:10px">{order.name}</div>
            <div style="font-size:11px;color:#9ca3af;margin-bottom:2px">Phone</div>
            <div style="font-size:14px;font-weight:700;color:#111">{order.phone}</div>
          </td>
          <td style="width:50%;vertical-align:top;padding-left:16px;border-left:1px solid #e5e7eb">
            <div style="font-size:11px;color:#9ca3af;margin-bottom:2px">Email</div>
            <div style="font-size:13px;color:#111;margin-bottom:10px">{order.email or 'Not provided'}</div>
            <div style="font-size:11px;color:#9ca3af;margin-bottom:2px">Delivery Address</div>
            <div style="font-size:12px;color:#374151;line-height:1.6;white-space:pre-line">{order.address}</div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- Items Table -->
  <tr>
    <td style="padding:20px 28px 0">
      <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;
                  color:#6b7280;border-bottom:1px solid #e5e7eb;padding-bottom:6px;margin-bottom:12px">
        Items Ordered
      </div>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border-collapse:collapse;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden">
        <thead>
          <tr style="background:#1f2937">
            <th style="padding:8px 12px;font-size:10px;text-align:left;color:#fff;
                       text-transform:uppercase;letter-spacing:.5px">Product</th>
            <th style="padding:8px 12px;font-size:10px;text-align:center;color:#fff;
                       text-transform:uppercase;letter-spacing:.5px">Qty</th>
            <th style="padding:8px 12px;font-size:10px;text-align:right;color:#fff;
                       text-transform:uppercase;letter-spacing:.5px">Amount</th>
          </tr>
        </thead>
        <tbody>
          {item_lines_html}
          {discount_html}
          <tr style="background:#f9fafb">
            <td colspan="2" style="padding:10px 12px;font-weight:700;font-size:14px;color:#111">Total</td>
            <td style="padding:10px 12px;font-weight:700;font-size:16px;color:#111;text-align:right">
              Rs.{float(order.total):.0f}
            </td>
          </tr>
        </tbody>
      </table>
    </td>
  </tr>

  <!-- CTA -->
  <tr>
    <td style="padding:20px 28px 24px;text-align:center">
      <a href="https://www.lakshmicrackers.com/admin/orders"
         style="display:inline-block;background:#b91c1c;color:#fff;padding:12px 28px;
                border-radius:8px;font-weight:700;font-size:13px;text-decoration:none;
                letter-spacing:.3px">
        View Order in Admin Panel
      </a>
      <p style="margin:12px 0 0;font-size:11px;color:#9ca3af">
        Call customer: <strong style="color:#111">{order.phone}</strong> to confirm payment
      </p>
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="background:#f9fafb;padding:14px 28px;text-align:center;
               border-top:1px solid #e5e7eb">
      <div style="font-size:11px;color:#9ca3af">
        Lakshmi Crackers Admin Notification &nbsp;|&nbsp; lakshmicrackersonline@gmail.com
      </div>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    try:
        msg = EmailMultiAlternatives(subject, plain_body, from_addr, [ADMIN_EMAIL])
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        logger.info('Admin notification sent to %s for order #%s', ADMIN_EMAIL, order.id)
        return True
    except Exception as exc:
        logger.warning(
            'Failed to send admin notification for order #%s: %s',
            order.id, exc
        )
        return False
