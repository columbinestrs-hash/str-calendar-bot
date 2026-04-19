from flask import Flask, request, jsonify
import calendar
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime, timedelta
import base64
import requests

app = Flask(__name__)

def generate_calendar(year, month, bookings):
    cell_w, cell_h = 110, 80
    header_h = 60
    day_label_h = 30
    cols = 7
    padding = 20

    first_weekday, days_in_month = calendar.monthrange(year, month)
    rows = ((first_weekday + days_in_month) + 6) // 7

    img_w = cols * cell_w + padding * 2
    img_h = header_h + day_label_h + rows * cell_h + padding * 2 + 30

    img = Image.new('RGB', (img_w, img_h), '#FFFFFF')
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except Exception:
        font = ImageFont.load_default()
        font_bold = font
        font_small = font

    month_name = datetime(year, month, 1).strftime('%B %Y')
    draw.text((img_w // 2, padding + 10), month_name, fill='#1a1a1a', font=font_bold, anchor='mm')

    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    for i, day in enumerate(days):
        x = padding + i * cell_w + cell_w // 2
        y = padding + header_h + day_label_h // 2
        draw.text((x, y), day, fill='#888888', font=font, anchor='mm')

    booking_map = {}
    for b in bookings:
        try:
            start = datetime.strptime(b['start'], '%Y-%m-%d')
            end = datetime.strptime(b['end'], '%Y-%m-%d')
            color = b.get('color', '#B5D4F4')
            text_color = b.get('text_color', '#0C447C')
            label = b.get('label', 'Guest')
            d = start
            while d < end:
                if d.month == month and d.year == year:
                    day_num = d.day
                    if day_num not in booking_map:
                        booking_map[day_num] = []
                    booking_map[day_num].append({
                        'color': color,
                        'text_color': text_color,
                        'label': label,
                        'is_start': d == start,
                        'is_end': (end - d).days == 1
                    })
                d += timedelta(days=1)
        except Exception as e:
            print(f"Booking parse error: {e}")
            continue

    today = datetime.now()

    for day in range(1, days_in_month + 1):
        pos = first_weekday + day - 1
        row = pos // 7
        col = pos % 7
        x = padding + col * cell_w
        y = padding + header_h + day_label_h + row * cell_h

        is_today = (day == today.day and month == today.month and year == today.year)
        border_color = '#378ADD' if is_today else '#E0E0E0'
        draw.rectangle([x+1, y+1, x+cell_w-1, y+cell_h-1],
                      outline=border_color, width=2 if is_today else 1)
        draw.text((x + 8, y + 8), str(day),
                 fill='#378ADD' if is_today else '#555555', font=font)

        if day in booking_map:
            for slot, bk in enumerate(booking_map[day]):
                bar_y = y + 30 + slot * 18
                bar_x_start = x + (4 if bk['is_start'] else 0)
                bar_x_end = x + cell_w - (4 if bk['is_end'] else 0)
                draw.rectangle([bar_x_start, bar_y, bar_x_end, bar_y + 14],
                               fill=bk['color'])
                if bk['is_start']:
                    draw.text((bar_x_start + 6, bar_y + 2), bk['label'],
                             fill=bk['text_color'], font=font_small)

    legend_y = img_h - 20
    legends = [('#B5D4F4', 'New booking'), ('#C0DD97', 'Existing booking')]
    lx = padding
    for color, label in legends:
        draw.rectangle([lx, legend_y - 10, lx + 12, l
