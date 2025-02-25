# We need this so Python doesn't complain about the unknown StableDiffusionProcessing-typehint at runtime
from __future__ import annotations

import csv
import os
import os.path
import typing
import collections.abc as abc
import tempfile
import shutil

#if typing.TYPE_CHECKING:
#    # Only import this when code is being type-checked, it doesn't have any effect at runtime
#    from .processing import StableDiffusionProcessing


class PromptStyle(typing.NamedTuple):
    name: str
    prompt: str
    negative_prompt: str
    long_description: str


def merge_prompts(style_prompt: str, prompt: str) -> str:
    if "{prompt}" in style_prompt:
        res = style_prompt.replace("{prompt}", prompt)
    else:
        parts = filter(None, (prompt.strip(), style_prompt.strip()))
        res = ", ".join(parts)

    return res


def apply_styles_to_prompt(prompt, styles):
    for style in styles:
        prompt = merge_prompts(style, prompt)

    return prompt


class StyleDatabase:
    def __init__(self, path: str, user_path: str):
        self.no_style = PromptStyle("None", "", "", "")
        self.styles = {}
        self.path = path
        self.user_path = user_path

        #print(path)
        self.reload()

    def reload(self):
        self.styles.clear()

        if not os.path.exists(self.path):
            print(f"Can't find styles at {self.path}")
        else:   
            with open(self.path, "r", encoding="utf-8-sig", newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    #print(f"row: {row}")
                    # Support loading old CSV format with "name, text"-columns
                    prompt = row["prompt"] if "prompt" in row else row["text"]
                    negative_prompt = row.get("negative_prompt", "")
                    long_description = row.get("long_description", "")
                    self.styles[row["name"]] = PromptStyle(row["name"], prompt, negative_prompt, long_description)

        if not os.path.exists(self.user_path):
            print(f"Can't find user styles at {self.user_path}")
        else:         
            with open(self.user_path, "r", encoding="utf-8-sig", newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    #print(f"row: {row}")
                    # Support loading old CSV format with "name, text"-columns
                    prompt = row["prompt"] if "prompt" in row else row["text"]
                    negative_prompt = row.get("negative_prompt", "")
                    long_description = row.get("long_description", "")
                    self.styles[row["name"]] = PromptStyle(row["name"], prompt, negative_prompt, long_description)

    def get_style_prompts(self, styles):
        return [self.styles.get(x, self.no_style).prompt for x in styles]

    def get_negative_style_prompts(self, styles):
        return [self.styles.get(x, self.no_style).negative_prompt for x in styles]

    def apply_styles_to_prompt(self, prompt, styles):
        return apply_styles_to_prompt(prompt, [self.styles.get(x, self.no_style).prompt for x in styles])

    def apply_negative_styles_to_prompt(self, prompt, styles):
        return apply_styles_to_prompt(prompt, [self.styles.get(x, self.no_style).negative_prompt for x in styles])

    def save_styles(self, path: str) -> None:
        # Always keep a backup file around
        if os.path.exists(path):
            shutil.copy(path, path + ".bak")

        fd = os.open(path, os.O_RDWR|os.O_CREAT)
        with os.fdopen(fd, "w", encoding="utf-8-sig", newline='') as file:
            # _fields is actually part of the public API: typing.NamedTuple is a replacement for collections.NamedTuple,
            # and collections.NamedTuple has explicit documentation for accessing _fields. Same goes for _asdict()
            writer = csv.DictWriter(file, fieldnames=PromptStyle._fields)
            writer.writeheader()
            writer.writerows(style._asdict() for k,     style in self.styles.items())
