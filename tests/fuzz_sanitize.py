#!/usr/bin/env python3
"""
Fuzzing harness for PII and secrets redaction module.
"""
import sys
import atheris

with atheris.instrument_imports():
    from vector_topic_modeling._sanitize import redact_pii_and_secrets


def TestOneInput(data):
    """
    Fuzzing entry point for testing redact_pii_and_secrets with arbitrary strings.
    """
    fdp = atheris.FuzzedDataProvider(data)
    text = fdp.ConsumeUnicodeNoSurrogates(len(data))
    redact_pii_and_secrets(text)


atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()
