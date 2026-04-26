#!/usr/bin/env python3
"""
扫描 pic/ 文件夹，读取照片和 .meta 元信息，生成 photos.json。

照片命名规则: YYYYMMDD_N.jpeg (如 20260424_0.jpeg)
元信息文件:   YYYYMMDD_N.meta (同名，三行文本)

用法: python3 build.py
"""

import json
import os
import re
import subprocess
import sys

PIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pic')
OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'photos.json')

PHOTO_PATTERN = re.compile(r'^(\d{8})_(\d+)\.(jpeg|jpg|png|webp)$', re.IGNORECASE)


def get_dimensions(filepath):
    """用 sips 获取图片宽高 (macOS)，失败则尝试 Pillow。"""
    try:
        out = subprocess.check_output(
            ['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', filepath],
            stderr=subprocess.DEVNULL, text=True
        )
        w = int(re.search(r'pixelWidth:\s*(\d+)', out).group(1))
        h = int(re.search(r'pixelHeight:\s*(\d+)', out).group(1))
        return w, h
    except Exception:
        pass
    try:
        from PIL import Image
        with Image.open(filepath) as img:
            return img.size
    except Exception:
        print(f'  警告: 无法读取 {os.path.basename(filepath)} 的尺寸，跳过')
        return None, None


def parse_meta(meta_path):
    """读取 .meta 文件，返回 dict。"""
    info = {'location': '', 'device': '', 'note': ''}
    if not os.path.exists(meta_path):
        return info
    with open(meta_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('地点:'):
                info['location'] = line[3:].strip()
            elif line.startswith('设备:'):
                info['device'] = line[3:].strip()
            elif line.startswith('备注:'):
                info['note'] = line[3:].strip()
    return info


def format_date(date_str):
    """'20250910' → '2025.09.10'"""
    return f'{date_str[:4]}.{date_str[4:6]}.{date_str[6:8]}'


def main():
    if not os.path.isdir(PIC_DIR):
        print(f'错误: 找不到 pic/ 文件夹')
        sys.exit(1)

    photos = []
    for fname in os.listdir(PIC_DIR):
        m = PHOTO_PATTERN.match(fname)
        if not m:
            continue

        date_str, seq, ext = m.group(1), m.group(2), m.group(3)
        filepath = os.path.join(PIC_DIR, fname)
        meta_path = os.path.join(PIC_DIR, f'{date_str}_{seq}.meta')

        w, h = get_dimensions(filepath)
        if w is None:
            continue

        meta = parse_meta(meta_path)

        photos.append({
            'src': f'pic/{fname}',
            'w': w,
            'h': h,
            'date': format_date(date_str),
            'location': meta['location'],
            'device': meta['device'],
            'note': meta['note'],
            '_sort': f'{date_str}_{seq}',
        })

    # 按日期从新到旧排序
    photos.sort(key=lambda p: p['_sort'], reverse=True)

    # 移除排序用的临时字段
    for p in photos:
        del p['_sort']

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(photos, f, ensure_ascii=False, indent=2)

    print(f'完成: 生成 {len(photos)} 张照片 → photos.json')


if __name__ == '__main__':
    main()
