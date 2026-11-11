# Copyright 2026 The LUCI Authors
# Use of this source code is governed under the Apache License, Version 2.0
# that can be found in the LICENSE file.

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from recipe_engine import post_process
from recipe_engine import recipe_test_api
from recipe_engine.recipe_api import RecipeScriptApi
from recipe_engine.recipe_test_api import RecipeTestApi
from RECIPE_MODULES.recipe_engine import (
    cipd,
    step,
)


@dataclass
class DEPS(RecipeScriptApi):
  cipd: cipd.API
  step: step.API


@dataclass
class TEST_DEPS(RecipeTestApi):
  step: step.TEST_API


def RunSteps(api: DEPS) -> None:
  # A failed install must not stay cached. The first ensure_tool call fails
  # (via mocked step data), and the second call for the same package should
  # run a fresh install rather than re-raise the first call's error.
  try:
    api.cipd.ensure_tool('infra/some_exe/${platform}', 'latest')
  except api.step.StepFailure:
    pass
  api.cipd.ensure_tool('infra/some_exe/${platform}', 'latest')


def GenTests(api: TEST_DEPS) -> Iterator[recipe_test_api.TestData]:
  yield api.test(
      'retry_after_failure',
      api.step_data('install infra/some_exe.ensure_installed', retcode=1),
      api.post_process(post_process.StepException,
                       'install infra/some_exe.ensure_installed'),
      api.post_process(post_process.StepSuccess,
                       'install infra/some_exe (2).ensure_installed'),
      api.post_process(post_process.DropExpectation),
  )
