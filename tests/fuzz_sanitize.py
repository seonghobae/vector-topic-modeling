#!/usr/bin/env python3
import sys
import atheris

with atheris.instrument_imports():
    from vector_topic_modeling._sanitize import redact_pii_and_secrets

def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    try:
        text = fdp.ConsumeUnicodeNoSurrogates(len(data))
    except Exception:
        return
    redact_pii_and_secrets(text)

atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()
