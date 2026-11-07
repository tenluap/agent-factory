#!/usr/bin/env python3
"""Compare a design reference PNG with an app capture of the same target.

Usage: python3 -P pixel-diff.py <reference.png> <capture.png> [options]

  --tolerance N    per-channel difference still treated as equal (default 24)
  --tile N         tile size in reference pixels for region detection (default 4)
  --min-share F    share of mismatching pixels that marks a tile (default 0.1,
                   which ignores 1 px anti-aliasing lines but flags 2 px shifts)
  --top N          number of regions to report (default 3)
  --montage FILE   write one PNG stacking the reported regions as reference | capture
  --crops DIR      write one side-by-side crop per reported region
  --max-diff PCT   exit 1 when the differing-pixel share exceeds PCT percent

Exit codes: 0 ok, 1 share above --max-diff, 2 input error (unreadable image or bad
arguments), 3 size mismatch (the capture is never resized).
Run with -P: numpy and Pillow live in the user site-packages, which -I disables.
Compare the numbers between repair rounds; view only the montage.
"""

import argparse
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image


def load(path):
    image = Image.open(path)
    if image.mode != "RGB":
        image = image.convert("RGBA")
        image = Image.alpha_composite(
            Image.new("RGBA", image.size, (255, 255, 255, 255)), image
        )
    return image.convert("RGB")


def find_regions(mask, tile, min_share):
    height, width = mask.shape
    rows, cols = -(-height // tile), -(-width // tile)
    padded = np.zeros((rows * tile, cols * tile), dtype=bool)
    padded[:height, :width] = mask
    counts = padded.reshape(rows, tile, cols, tile).sum(axis=(1, 3))
    hot = counts >= max(2, min_share * tile * tile)
    seen = np.zeros_like(hot)
    regions = []
    for row in range(rows):
        for col in range(cols):
            if not hot[row, col] or seen[row, col]:
                continue
            seen[row, col] = True
            queue = deque([(row, col)])
            top, bottom, left, right, pixels = row, row, col, col, 0
            while queue:
                y, x = queue.popleft()
                pixels += int(counts[y, x])
                top, bottom, left, right = (
                    min(top, y),
                    max(bottom, y),
                    min(left, x),
                    max(right, x),
                )
                for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if (
                        0 <= ny < rows
                        and 0 <= nx < cols
                        and hot[ny, nx]
                        and not seen[ny, nx]
                    ):
                        seen[ny, nx] = True
                        queue.append((ny, nx))
            x0, y0 = left * tile, top * tile
            box = (
                x0,
                y0,
                min((right + 1) * tile, width) - x0,
                min((bottom + 1) * tile, height) - y0,
            )
            regions.append((pixels, box))
    regions.sort(key=lambda region: region[0], reverse=True)
    return regions


def region_pairs(reference, capture, regions, margin=8):
    pairs = []
    for _, (x, y, w, h) in regions:
        box = (
            max(x - margin, 0),
            max(y - margin, 0),
            min(x + w + margin, reference.width),
            min(y + h + margin, reference.height),
        )
        pairs.append((reference.crop(box), capture.crop(box)))
    return pairs


def write_montage(pairs, path):
    width = max(left.width * 2 + 4 for left, _ in pairs)
    height = sum(left.height for left, _ in pairs) + 8 * (len(pairs) - 1)
    sheet = Image.new("RGB", (width, height), (255, 0, 255))
    top = 0
    for left, right in pairs:
        sheet.paste(left, (0, top))
        sheet.paste(right, (left.width + 4, top))
        top += left.height + 8
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)
    return path


def write_crops(pairs, directory):
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, (left, right) in enumerate(pairs, start=1):
        pair = Image.new("RGB", (left.width * 2 + 4, left.height), (255, 0, 255))
        pair.paste(left, (0, 0))
        pair.paste(right, (left.width + 4, 0))
        path = directory / f"region-{index}.png"
        pair.save(path)
        paths.append(path)
    return paths


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("reference")
    parser.add_argument("capture")
    parser.add_argument("--tolerance", type=int, default=24)
    parser.add_argument("--tile", type=int, default=4)
    parser.add_argument("--min-share", type=float, default=0.1)
    parser.add_argument("--top", type=int, default=3)
    parser.add_argument("--montage", type=Path)
    parser.add_argument("--crops", type=Path)
    parser.add_argument("--max-diff", type=float)
    args = parser.parse_args()

    try:
        reference, capture = load(args.reference), load(args.capture)
    except (OSError, ValueError) as error:
        print(f"input error: {error}", file=sys.stderr)
        sys.exit(2)
    print(
        f"reference {reference.width}x{reference.height}, "
        f"capture {capture.width}x{capture.height}"
    )
    if capture.size != reference.size:
        print(
            "size mismatch: fix the capture viewport or scale; the capture is never resized",
            file=sys.stderr,
        )
        sys.exit(3)

    delta = np.abs(
        np.asarray(reference, dtype=np.int16) - np.asarray(capture, dtype=np.int16)
    ).max(axis=2)
    mask = delta > args.tolerance
    share = mask.mean() * 100
    print(f"differing pixels: {share:.2f}% (tolerance {args.tolerance})")

    regions = find_regions(mask, args.tile, args.min_share)
    shown = regions[: args.top]
    print(f"regions: {len(regions)} (showing {len(shown)})")
    for index, (pixels, (x, y, w, h)) in enumerate(shown, start=1):
        print(f"  {index}. x={x} y={y} w={w} h={h} pixels={pixels}")
    if shown:
        pairs = region_pairs(reference, capture, shown)
        if args.montage:
            print(f"montage: {write_montage(pairs, args.montage)}")
        if args.crops:
            for path in write_crops(pairs, args.crops):
                print(f"crop: {path}")

    if args.max_diff is not None and share > args.max_diff:
        sys.exit(1)


if __name__ == "__main__":
    main()
