#!/usr/bin/env python
# -*- coding: utf-8 -*-

ticks = list(u'▁▂▃▄▅▆▇█')


def tick(value, min_val, max_val):
    if min_val == max_val:
        return ticks[0]
    tick_id = len(ticks) * (value - min_val) / (max_val - min_val)
    if tick_id == len(ticks):
        tick_id -= 1
    return ticks[tick_id]


def average(values):
    return sum(values) / len(values)


def iaggregate(series, target_length, func=average):
    chunk_size = 1.0 * len(series) / target_length
    chunk_start = 0
    chunk_id = 0
    while chunk_start < len(series):
        chunk_id += 1
        chunk_end = int(chunk_id * chunk_size)
        yield func(series[chunk_start:chunk_end])
        chunk_start = chunk_end


def aggregate(series, target_length, func=average):
    return list(iaggregate(series, target_length, func))


def sparkline(series):
    max_val = max(series)
    min_val = min(series)
    if min_val > 0:
        min_val = 0
    return ''.join(tick(i, min_val, max_val) for i in series)