"""
title: IPA Translator OpenAPI Server
author: lotusfa.com
author_url: https://lotusfa.com
version: 0.1.0
description: A RESTful API for converting words to their IPA representation. Providing tools for AI in open webui to call
js_version_url: https://toolbox.lotusfa.com/ipa/cantonese/index.html
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import json

from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Literal
import pytz
from dateutil import parser as dateutil_parser
from pathlib import Path
from typing import Optional, Dict, List

app = FastAPI(
    title="IPA Translator Utilities API",
    version="1.0.0",
    description="Transform any word, phrase, or sentence into its precise International Phonetic Alphabet (IPA) representation ",
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Helper Functions
# -------------------------------

available_formats = ["org", "num", "Jyutping"]

source_dict = {
    "yue":      ("Cantonese",            "yue.json"),
    "en_UK":    ("English (UK)",         "en_UK.json"),
    "en_US":    ("English (US)",         "en_US.json"),
    "eo":       ("Esperanto",            "eo.json"),
    "fr_FR":    ("French (FR)",          "fr_FR.json"),
    "fr_QC":    ("French (QC)",          "fr_QC.json"),
    "ja":       ("Japanese",             "ja.json"),
    "zh_hans":  ("Mandarin (Hans)",      "zh_hans.json"),
    "zh_hant":  ("Mandarin (Hant)",      "zh_hant.json"),
    "fa":       ("Persian",              "fa.json"),
    "es_ES":    ("Spanish (ES)",         "es_ES.json"),
    "es_MX":    ("Spanish (MX)",         "es_MX.json"),
}

def _load_ipa_dict(lang_code: str) -> Dict[str, str]:
    """
    Return the JSON mapping used by the original JS (`get_IPA_DB`).
    The files live under the ./data/ directory 
    """

    if lang_code not in source_dict:
        raise ValueError(f'Unsupported language code: {lang_code}')

    _, filename = source_dict[lang_code]
    json_path = Path("./data") / filename
    with json_path.open(encoding="utf-8") as f:
        return json.load(f) 
    
# ----------------------------------------------------------------------
# Core translator – this is the real implementation that replaces the
# placeholder in source [2].
# ----------------------------------------------------------------------

def translate_to_ipa(
        input_string: str, 
        lang_code: str,
        show_word_form: bool = False,
        output_format: str = "org"
    ) -> str:
    
    if (lang_code in ["zh_hans", "yue", "zh_hant"]):
        return _translate_to_ipa_zh(input_string, lang_code, show_word_form, output_format)
    else:
        return _translate_to_ipa_en(input_string, lang_code, show_word_form)

def _translate_to_ipa_en(
        input_string: str, 
        lang_code: str,
        show_word_form: bool = False
    ) -> str:

    """
    Translate an English input string to IPA.

      1. Split the input text into separate words.
      2. Pre‑process each word (lower‑case, strip punctuation) using
         ``_preprocess_eng`` – this is the same transformation the JS code
         applies via ``preprocess_eng``.
      3. Look the pre‑processed word up in the language‑specific IPA
         dictionary loaded by ``_load_ipa_dict``.
      4. If a match is found, use the IPA transcription; otherwise keep the
         original word.
      5. Join the results with spaces (the JS version would also optionally
         wrap the original word and its IPA in “( word : ipa )”, but the
         Python API does not expose the “show_word_form” flag, so we simply
         return the IPA or the original token).

    Parameters
    ----------
    input_string: str
        The raw English text to be transcribed.
    lang_code: str
        Language code (e.g. ``"en_US"`` or ``"en_UK"``); must be present in
        ``source_dict``.

    Returns
    -------
    str
        Space‑separated IPA transcription (or original words where no
        transcription exists).
    """
    # Load the English IPA dictionary.
    ipa_dict = _load_ipa_dict(lang_code)

    # Split the input on whitespace – this reproduces the
    # ``(get_IPA_tBox()+" ").split(" ");`` behaviour.
    words = input_string.split()

    result_parts: list[str] = []

    for word in words:
        if word == "":
            continue

        # Apply the same preprocessing the JS code does.
        t_word = _preprocess_eng(word)

        # Look up the pre‑processed token in the dictionary.
        if t_word in ipa_dict:
            ipa = ipa_dict[t_word]
            # result_parts.append(ipa)
            result_parts.append(f"{t_word}/{ipa}/" if show_word_form else f"/{ipa}/")
        else:
            # No entry – keep the original word unchanged.
            result_parts.append(word)

    # Re‑assemble the final string (the JS code updates the text box after each
    # iteration; here we return the complete result at once).
    return " ".join(result_parts)


def _translate_to_ipa_zh(
        input_string: str, 
        lang_code: str,
        show_word_form: bool = False,
        output_format: str = "org"
        ) -> str:
    """

    Parameters
    ----------
    input_string: str
        The raw text entered by the user.
    lang_code: str
        Language identifier – must exist in the `source_dict` mapping.
    show_word_form: bool, optional
        When True, the returned string includes the original characters
        before the IPA (e.g. `char/IPA/`). Mirrors the `wf_c_words`
        checkbox in the UI.
    output_format: {"org", "num", "jyutping"}
        Determines which of the three formatting functions from the JS
        file should be applied (see source [1]).

    Returns
    -------
    str
        The formatted IPA transcription.
    """
    # Load the language‑specific mapping.
    ipa_dict = _load_ipa_dict(lang_code)

    allow_words_search = True

    # Work on a list of characters so we can advance the index manually.
    chars = list(input_string)
    i = 0
    result_parts = []

    while i < len(chars):
        ch = chars[i]

        # Direct character lookup – if not present we just copy the char.
        if ch in ipa_dict:
            # Simple case: single‑character match.
            ipa = ipa_dict[ch]
            result_parts.append(f"{ch}/{ipa}/" if show_word_form else f"/{ipa}/")
            i += 1
            continue

        # --- allow‑words‑search branch (mirrors the JS block) ---
        if allow_words_search:
            # Build candidate substrings up to length 6.
            candidates = ["".join(chars[i:i+L]) for L in range(1, 7)
                          if i + L <= len(chars)]
            # Find the longest candidate that exists in the dict.
            match = None
            for cand in reversed(candidates):          # longest first
                if cand in ipa_dict:
                    match = cand
                    break

            if match:
                ipa = ipa_dict[match]
                result_parts.append(f"{match}/{ipa}/" if show_word_form else f"/{ipa}/")
                i += len(match)
                continue

        # No match – copy the original character (or space) verbatim.
        result_parts.append(ch)
        i += 1

    # Join everything into a single string.
    raw_result = "".join(result_parts)

    # Apply the requested output format.
    if output_format == "num":
        return _format_ipa_num(raw_result)
    elif output_format == "jyutping":
        return _format_jyutping(raw_result)
    else:   # "org"
        return _format_ipa_org(raw_result)
    

# ----------------------------------------------------------------------
# Formatting helpers – they reproduce the three format_* functions from
# the JS file (source [1]).
# ----------------------------------------------------------------------

def _preprocess_eng(text: str) -> str:
    """
    Replicates the JS `preprocess_eng` logic:
    * Convert all A‑Z to lower‑case a‑z
    * Remove '.' ',' and newline characters
    """
    # Lower‑case the alphabetic characters
    text = text.translate(str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "abcdefghijklmnopqrstuvwxyz"
    ))
    # Strip punctuation and line breaks
    for ch in ".\n,":
        text = text.replace(ch, "")
    return text

def _format_ipa_num(txt: str) -> str:
    """Replace tone symbols with numeric tones."""
    return (
        txt.replace("˥", "5")
           .replace("˧", "3")
           .replace("˨", "2")
           .replace("˩", "1")
           .replace(":", "")
    )

def _format_jyutping(txt: str) -> str:
    """Convert the Cantonese tone marks to Jyutping numbers."""
    replacements = [
        ("˥˧", "1"), ("˥˥", "1"),
        ("˧˥", "2"), ("˧˥", "2"),
        ("˧˧", "3"),
        ("˨˩", "4"), ("˩˩", "4"),
        ("˩˧", "5"), ("˨˧", "5"),
        ("˨˨", "6"),
        ("k˥", "k7"), ("k˧", "k8"), ("k˨", "k9"),
        ("t˥", "t7"), ("t˧", "t8"), ("t˨", "t9"),
        ("p˥", "p7"), ("p˧", "p8"), ("p˨", "p9"),
        ("˥", "1"), ("˧", "3"), ("˨", "6"),
        (":", "")
    ]
    for old, new in replacements:
        txt = txt.replace(old, new)
    return txt

def _format_ipa_org(txt: str) -> str:
    """Original format – no changes."""
    return txt

# -------------------------------
# Pydantic models
# -------------------------------

class IpaResponse(BaseModel):
    ipa: str = Field(..., description="IPA transcription of the input")
    format: str = Field("", description="Echoed format field (currently unused)")

class IpaRequest(BaseModel):
    input_string: str = Field(..., description="Text to be transcribed")
    lang_code: str = Field(..., description="Language code, e.g. \"en_US\"")
    format: Optional[str] = Field(
        "", description="Desired output format – ignored for now, defaults to \"\""
    )
    show_word_form: Optional[bool] = Field(
        False, description="Whether to show word form or not"
    )

# -------------------------------
# Routes
# -------------------------------

@app.get(
    "/list_all_format",
    summary="List all available format",
    response_model=Dict[str, List[str]],
)
def list_all_format() -> Dict[str, List[str]]:
    """
    Return a JSON object that enumerates every output format the
    service can produce.  The values correspond to the three formatting
    helpers defined in the original JavaScript file
    (`format_IPA_org`, `format_IPA_num`, `format_Jyutping`).
    """
    if not available_formats:          # defensive – should never happen
        raise HTTPException(
            status_code=500,
            detail="No formats are configured – internal configuration error."
        )
    return {"formats": available_formats}

@app.get(
    "/list_all_language",
    summary="List all available languages",
    response_model=Dict[str, List[str]],
)
def list_all_language() -> Dict[str, List[str]]:
    """
    Return a JSON object that contains every language **index** that the
    service knows about.
    """
    lang_key: List[str] = list(source_dict.keys())

    if not lang_key:                     # Defensive – should never happen
        raise HTTPException(
            status_code=500,
            detail="Language mapping is empty – internal configuration error."
        )

    return {"languages": lang_key}

@app.post(
    "/ipa",
    summary="Convert an input string to IPA for a given language",
    response_model=IpaResponse,
)
def get_ipa(payload: IpaRequest) -> IpaResponse:
    """
    **POST** endpoint that receives:

    * ``input_string`` – text to be transcribed,
    * ``lang_code`` – one of the language indexes you expose,
    * ``format`` – optional (currently ignored, defaults to ``\"\"``).

    The endpoint returns the IPA representation of the input string.
    """
    if payload.lang_code not in source_dict:
        raise HTTPException(
            status_code=400,
            detail=f'Unsupported language code "{payload.lang_code}". '
                   f'Available codes: {list(source_dict.keys())}',
        )

    try:

        ipa_result = translate_to_ipa(
            payload.input_string,
            payload.lang_code,
            payload.show_word_form,
            payload.format
        )      # "org", "num", or "jyutping"
        

        # ipa_result = translate_to_ipa(payload.input_string, payload.lang_code)
    except Exception as exc:  # catch any unexpected error from the library
        raise HTTPException(
            status_code=500,
            detail=f"IPA translation failed: {str(exc)}",
        ) from exc

    return IpaResponse(ipa=ipa_result, format=payload.format or "")