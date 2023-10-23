# Changelog

All notable changes to this project will be documented in this file. See
[Conventional Commits](https://conventionalcommits.org) for commit guidelines.

## [0.21.0](https://github.com/svange/openbrain/compare/v0.20.0...v0.21.0) (2023-10-17)


### Features

* demote many info log statements to debug statements ([6dee4bb](https://github.com/svange/openbrain/commit/6dee4bba5c6baf2bc793661d1af0c65403a3a39c))

## [0.20.0](https://github.com/svange/openbrain/compare/v0.19.0...v0.20.0) (2023-10-17)


### Features

* remove promptlayer support ([d99e26e](https://github.com/svange/openbrain/commit/d99e26eef05c3eb31dd26f5aed513262282148ae))

## [0.19.0](https://github.com/svange/openbrain/compare/v0.18.1...v0.19.0) (2023-10-16)


### Features

* Fallback scheme for environment variables and better output when initializing. ([d797a8b](https://github.com/svange/openbrain/commit/d797a8bf040485eacf6c3259b30d0bc61dd13b65))
* Fallback scheme for environment variables and better output when initializing. ([498b92e](https://github.com/svange/openbrain/commit/498b92ec029f1f95e66a74f54d07b74138961f53))


### Bug Fixes

* another attempt to fix ci/cd pipeline env vars ([90f0fa0](https://github.com/svange/openbrain/commit/90f0fa0e4b0b7d1f9513cd1f5ef8d9dd7a29bf88))
* ci/cd env vars for new scheme. ([d5ef7af](https://github.com/svange/openbrain/commit/d5ef7af09ad71c55dde86c3ab24ac99d1e9a03b3))
* fixed __init__.py environment auto-setup for ci/cd ([3ad3042](https://github.com/svange/openbrain/commit/3ad3042a2350a187162085e44ec8534198868a9e))
* repaired and improved cli tools except for ob-chat ([3908a38](https://github.com/svange/openbrain/commit/3908a38d9a06be011d11a78b74ba5b88f1df9b43))
* repaired and improved cli tools except for ob-chat ([c8c0729](https://github.com/svange/openbrain/commit/c8c0729830bc64fa21283a771bbc7e9ab2d5ac90))

## [0.18.1](https://github.com/svange/openbrain/compare/v0.18.0...v0.18.1) (2023-10-08)


### Bug Fixes

* ob-tuner PORT type error. ([98b0f3c](https://github.com/svange/openbrain/commit/98b0f3cffb32d0de394c69dd03f26425cb420ca4))

## [0.18.0](https://github.com/svange/openbrain/compare/v0.17.1...v0.18.0) (2023-10-08)


### Features

* add GRADIO_PORT env var to allow a single instance to host several gradios ([8f45495](https://github.com/svange/openbrain/commit/8f4549582cb7d0a14c8a7dea9ff9daca8105dc4e))

## [0.17.1](https://github.com/svange/openbrain/compare/v0.17.0...v0.17.1) (2023-10-06)


### Bug Fixes

* fixing ci/cd so pre-releases don't always release. ([f724422](https://github.com/svange/openbrain/commit/f7244220be1a1da43979bce421383ffd41e4c0bd))

## [0.17.0](https://github.com/svange/openbrain/compare/v0.16.0...v0.17.0) (2023-10-06)


### Features

* `ob-chat` works with in-memory DB out-of-the-box. ([558d44b](https://github.com/svange/openbrain/commit/558d44bf495a3d4d440cdd085688f8e22dea464b))

## [0.16.0](https://github.com/svange/openbrain/compare/v0.15.1...v0.16.0) (2023-10-04)


### Features

* ob-tuner updated to use in memory ORM, controllable by .env file. ([47ba771](https://github.com/svange/openbrain/commit/47ba771399c37bc4e07a56db1b561da035e5a5ed))

## [0.15.1](https://github.com/svange/openbrain/compare/v0.15.0...v0.15.1) (2023-10-04)


### Bug Fixes

* added more granularity to CI/CD system and attempting to bring prereleases. ([8316019](https://github.com/svange/openbrain/commit/83160190224d043e9663cf47fbe7b2c381fb586c))
* added more granularity to CI/CD system and attempting to bring prereleases. ([f4e02ea](https://github.com/svange/openbrain/commit/f4e02ea9d53899068336d765bfa815b6a199ef40))
* updating CI/CD ([937d34b](https://github.com/svange/openbrain/commit/937d34b65f22210e808546cc5afd7bd48f76acad))

## [0.15.0](https://github.com/svange/openbrain/compare/v0.14.1...v0.15.0) (2023-10-01)


### Features

* demote gradio to be an optional dependency so that package fits in lambdas by default. Install with -E to get gradio. ([0595a08](https://github.com/svange/openbrain/commit/0595a083b06edf1e82efefc50640ef2d460b820c))

## [0.14.1](https://github.com/svange/openbrain/compare/v0.14.0...v0.14.1) (2023-09-30)


### Bug Fixes

* support python 3.10 by resolving dependencies for python 3.10 (pydantic_core module missing issue). Second attempt :( ([52c4545](https://github.com/svange/openbrain/commit/52c4545dfd8304b3bcf958c680b392abccfbed7f))

## [0.14.0](https://github.com/svange/openbrain/compare/v0.13.0...v0.14.0) (2023-09-30)


### Features

* support python 3.10 by resolving dependencies for python 3.10 (pydantic_core module missing issue). ([1fe40b4](https://github.com/svange/openbrain/commit/1fe40b42a5981add67414e65d03e414e11735dbf))


### Bug Fixes

* support python 3.10 by resolving dependencies for python 3.10 (pydantic_core module missing issue). ([4a59dfb](https://github.com/svange/openbrain/commit/4a59dfb22ed256ffd5654603e067153a3522ce03))

## [0.13.0](https://github.com/svange/openbrain/compare/v0.12.0...v0.13.0) (2023-09-29)


### Features

* in memory DB for locally running full system. ([f0ba078](https://github.com/svange/openbrain/commit/f0ba078ba70c8c5152d258349cfd707bbc454073))

## [0.12.0](https://github.com/svange/openbrain/compare/v0.11.1...v0.12.0) (2023-09-27)


### Features

* created ci_cd test set to stop my api keys from getting revoked. ([af9643e](https://github.com/svange/openbrain/commit/af9643eaf030fcbd2385059fdfc40276ce925316))


### Bug Fixes

* CI/CD pipeline and migrate to poetry. ([b6d1bf4](https://github.com/svange/openbrain/commit/b6d1bf4fbf5d90e95b9ff5c98893510c8c4ac594))

## [0.12.0](https://github.com/svange/openbrain/compare/v0.11.1...v0.12.0) (2023-09-27)


### Features

* created ci_cd test set to stop my api keys from getting revoked. ([af9643e](https://github.com/svange/openbrain/commit/af9643eaf030fcbd2385059fdfc40276ce925316))


### Bug Fixes

* CI/CD pipeline and migrate to poetry. ([b6d1bf4](https://github.com/svange/openbrain/commit/b6d1bf4fbf5d90e95b9ff5c98893510c8c4ac594))

## [0.11.1](https://github.com/svange/openbrain/compare/v0.11.0...v0.11.1) (2023-09-26)


### Bug Fixes

* CI/CD and style enforced, preparing to make public. ([2793298](https://github.com/svange/openbrain/commit/2793298bfa0756c1d82d1add706759e71dd0fca3))

## [0.11.1](https://github.com/svange/openbrain/compare/v0.11.0...v0.11.1) (2023-09-26)


### Bug Fixes

* CI/CD and style enforced, preparing to make public. ([2793298](https://github.com/svange/openbrain/commit/2793298bfa0756c1d82d1add706759e71dd0fca3))

## [0.11.1](https://github.com/svange/openbrain/compare/v0.11.0...v0.11.1) (2023-09-26)


### Bug Fixes

* CI/CD and style enforced, preparing to make public. ([2793298](https://github.com/svange/openbrain/commit/2793298bfa0756c1d82d1add706759e71dd0fca3))

## [0.11.1](https://github.com/svange/openbrain/compare/v0.11.0...v0.11.1) (2023-09-26)


### Bug Fixes

* CI/CD and style enforced, preparing to make public. ([2793298](https://github.com/svange/openbrain/commit/2793298bfa0756c1d82d1add706759e71dd0fca3))

## [0.11.0](https://github.com/svange/openbrain/compare/v0.10.8...v0.11.0) (2023-09-25)


### Features

* CI/CD pipeline is ready! Semantic motherfucking releases!!! ([64134be](https://github.com/svange/openbrain/commit/64134bee1dde452e5314448c900531ef45c38357))

## [0.10.8](https://github.com/svange/openbrain/compare/v0.10.7...v0.10.8) (2023-09-25)


### Bug Fixes

* disabled pytest temporarily ([098aca8](https://github.com/svange/openbrain/commit/098aca8f85c210e9dad6ccf8e373574bf502401a))

## [0.10.7](https://github.com/svange/openbrain/compare/v0.10.6...v0.10.7) (2023-09-25)


### Bug Fixes

* disabled pytest temporarily ([9b2db9f](https://github.com/svange/openbrain/commit/9b2db9fc00bde9695177a2f1dc9ee471cf61ffc3))

## [0.10.6](https://github.com/svange/openbrain/compare/v0.10.5...v0.10.6) (2023-09-25)


### Bug Fixes

* ci/cd ([6a1ff5f](https://github.com/svange/openbrain/commit/6a1ff5f9867e13694b660fde71d99288c3cbfbe4))
* ci/cd ([af9778e](https://github.com/svange/openbrain/commit/af9778e46f6f593386063dd497332c02dd852867))
* ci/cd ([ea0693e](https://github.com/svange/openbrain/commit/ea0693ef4963d0f1a8d57fcf9c1ce79dafee67ff))
* ci/cd ([b1f8d86](https://github.com/svange/openbrain/commit/b1f8d86f78dccb8e8f90b6ffcf5cbfdf46dba45b))
* ci/cd ([a5c6a90](https://github.com/svange/openbrain/commit/a5c6a90c78c70f9eae535c20b3d263509f57d444))
* ci/cd ([bcaec4b](https://github.com/svange/openbrain/commit/bcaec4b8504bd80529ae75e92d4f9c261f1fa2ce))
* disabled pytest temporarily ([d80c08c](https://github.com/svange/openbrain/commit/d80c08c7634e0d62b95cd81806a40cd6bdfc143e))
* disabled pytest temporarily ([4c2e885](https://github.com/svange/openbrain/commit/4c2e8852b9bcd2f2991e89bfb4fd9ce7d73a9d27))
* disabled pytest temporarily ([4de360f](https://github.com/svange/openbrain/commit/4de360fe306efa28832dba58ddc3b9e00e7b78fd))
* disabled pytest temporarily ([6f66003](https://github.com/svange/openbrain/commit/6f66003cfda18d02250e71146764c72362fbc99e))
* removing references to commitizen repo ([be3b8de](https://github.com/svange/openbrain/commit/be3b8deeef3315af784b28d95f23df1d05df7ea9))


### Performance Improvements

* disabled pytest temporarily ([ccdb6bc](https://github.com/svange/openbrain/commit/ccdb6bc8fcb2e6c091523132e4aea3e2cba8e103))
* disabled pytest temporarily ([7cc2dfa](https://github.com/svange/openbrain/commit/7cc2dfa6a49eae143c0c92f7986b317c578bef16))
* disabled pytest temporarily ([f40db8e](https://github.com/svange/openbrain/commit/f40db8e294a50e3b6fd4d9bad97027addd73afcf))
* disabled pytest temporarily ([9013b3c](https://github.com/svange/openbrain/commit/9013b3c601b9824f39a131fe167d44161cd3e3ba))

# CHANGELOG



## v0.10.3 (2023-09-24)

### Fix

- update ci and deps
- update ci and deps

## v0.10.2 (2023-09-24)

### Fix

- disabling test-pypi for now

## v0.10.1 (2023-09-24)

### Fix

- disabling test-pypi for now

## v0.10.0 (2023-09-24)

### Feat

- adding dev branch back into ci/cd
- adding dev branch back into ci/cd
- adding dev branch back into ci/cd
- adding dev branch back into ci/cd

## v0.9.0 (2023-09-24)

### Feat

- adding dev branch back into ci/cd

### Fix

- removing references to commitizen repo
- changing refs to master branch to main

## v0.8.0 (2023-09-24)

### Feat

- commitizen

## v0.7.0 (2023-09-24)


## v0.6.0 (2023-09-24)


## v0.5.1 (2023-09-24)

### Unknown

* lets try commitizen and sematic releases ([`1bbb25f`](https://github.com/svange/openbrain/commit/1bbb25ffc7c3e5dcaaff37731d0581320cbf3dea))


## v0.5.0 (2023-09-24)

### Unknown

* Merge pull request #35

* chat cli wip #pr

* reverting to older working config for ci/cd pipeline

* fix: pipeline semantic-release

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* chore(release): 0.4.12 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* chore(release): 0.4.13 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* chore(release): 0.4.14 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* chore(release): 0.4.15 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* chore(release): 0.4.16 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* chore(release): 0.4.17 [skip ci]

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* chore(release): 0.4.18 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* Merge branch &#39;main&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* Merge branch &#39;main&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr ([`d0bbdeb`](https://github.com/svange/openbrain/commit/d0bbdeb54f42f5a80f8a101bf08a214d34342cdf))

* Merge pull request #34

* chat cli wip #pr

* reverting to older working config for ci/cd pipeline

* fix: pipeline semantic-release

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* chore(release): 0.4.12 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* chore(release): 0.4.13 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* chore(release): 0.4.14 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* chore(release): 0.4.15 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* chore(release): 0.4.16 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* chore(release): 0.4.17 [skip ci]

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* chore(release): 0.4.18 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* Merge branch &#39;main&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr ([`0f575f1`](https://github.com/svange/openbrain/commit/0f575f11f9f5fa05ce2befe4e26c08508e035901))

* Merge pull request #33

* chat cli wip #pr

* reverting to older working config for ci/cd pipeline

* fix: pipeline semantic-release

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* chore(release): 0.4.12 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* chore(release): 0.4.13 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* chore(release): 0.4.14 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* chore(release): 0.4.15 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* chore(release): 0.4.16 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* chore(release): 0.4.17 [skip ci]

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr

* chore(release): 0.4.18 [skip ci]

* Merge branch &#39;dev&#39; of github.com:/svange/openbrain into dev

* fix: pipeline semantic-release #pr

* fix: pipeline semantic-release #pr ([`8f9ff2e`](https://github.com/svange/openbrain/commit/8f9ff2e3c8f8fc31bfe6ff71de335c73a9aee0a4))

* Merge pull request #32

PR ci/dev -&gt; main ([`9df186f`](https://github.com/svange/openbrain/commit/9df186f5b8a317baa0755caf69dbe67602ba47de))

* chat cli wip #pr ([`1c8d172`](https://github.com/svange/openbrain/commit/1c8d17262757f333e09d77ce8b56ae0809096397))

* add gh_pat env var ([`ac87fa6`](https://github.com/svange/openbrain/commit/ac87fa6c582e83b9fcb145b0682bebd0647d588c))


## v0.4.11 (2023-09-23)

### Chore

* chore(release): 0.4.11 [skip ci]

## [0.4.11](https://github.com/svange/openbrain/compare/v0.4.10...v0.4.11) (2023-09-23)

### Bug Fixes

* github actions ([ef1c1fc](https://github.com/svange/openbrain/commit/ef1c1fcc1d0d65fcb004c066d642a5b3e99c5235))
* github actions bux fixes ([072805b](https://github.com/svange/openbrain/commit/072805b0dffc558a9a067df1265ec839e2c72e35)) ([`6a2f731`](https://github.com/svange/openbrain/commit/6a2f7317edaeb52d477e403b74f51605986c8c0b))

### Fix

* fix: github actions bux fixes ([`072805b`](https://github.com/svange/openbrain/commit/072805b0dffc558a9a067df1265ec839e2c72e35))

* fix: github actions ([`ef1c1fc`](https://github.com/svange/openbrain/commit/ef1c1fcc1d0d65fcb004c066d642a5b3e99c5235))

### Unknown

* Merge pull request #31

PR ci/dev -&gt; main ([`9141165`](https://github.com/svange/openbrain/commit/9141165cf3f865be67e78274d51c8cfac268a729))

* updating pipeline for work on dev branch #pr ([`75ac93a`](https://github.com/svange/openbrain/commit/75ac93afbf7ce6b249a2cfb86d0d025426ac0e22))

* Merge branch &#39;main&#39; of github.com:/svange/openbrain into dev

# Conflicts:
#	.github/workflows/dev.yml ([`caaa765`](https://github.com/svange/openbrain/commit/caaa7655828c6e2499fa6d3c1ae850c564cca54d))

* updating pipeline for work on dev branch #pr ([`f5860fd`](https://github.com/svange/openbrain/commit/f5860fd7d696dac0d8170a6aababb1e13b48014f))

* updating pipeline for work on dev branch #pr ([`96f1331`](https://github.com/svange/openbrain/commit/96f1331ba9142824c9ca30f74d4373878220d8c0))

* Merge pull request #30

* updating pipeline for work on dev branch #test #pr ([`bd23f33`](https://github.com/svange/openbrain/commit/bd23f33a69138dded3a692c324fef4b7c6063713))

* updating pipeline for work on dev branch #test #pr ([`61c565b`](https://github.com/svange/openbrain/commit/61c565b57f57fe8e0be597b77273d4a9da15eb59))

* Merge branch &#39;fix/pipeline-not-releasing-on-master-only-on-refs&#39; of github.com:/svange/openbrain

# Conflicts:
#	.github/workflows/semantic-branches.yml ([`f39698b`](https://github.com/svange/openbrain/commit/f39698b32658d36b0786497887998c3a9bf5be9b))

* stopping pr from triggering conditionally, just always pr, hopefully, each branch will just have a single, updating PR. ([`b0719cb`](https://github.com/svange/openbrain/commit/b0719cb51ae4b0eddd75ef2bf2b304b83109310d))

* Merge pull request #29

* Fixing pipeline

* Merge branch &#39;main&#39; of github.com:/svange/openbrain into fix/pipeline…

* trying regex in pyproject.toml #pr

* trying regex in pyproject.toml

* Merge remote-tracking branch &#39;origin/fix/pipeline-not-releasing-on-ma…

* bugfixing #pr

* bugfixing

* Merge remote-tracking branch &#39;origin/fix/pipeline-not-releasing-on-ma…

* bugfixing #pr

* bugfixing #pr

* bugfixing #pr

* Merge remote-tracking branch &#39;origin/fix/pipeline-not-releasing-on-ma…

* bugfixing #pr ([`99d2e42`](https://github.com/svange/openbrain/commit/99d2e42b2bb32d75db93586224f8947e2e0a9f2b))

* bugfixing #pr ([`4914654`](https://github.com/svange/openbrain/commit/4914654cd188877a652675b721b3e37290d2c2d7))

* Merge remote-tracking branch &#39;origin/fix/pipeline-not-releasing-on-master-only-on-refs&#39; into fix/pipeline-not-releasing-on-master-only-on-refs ([`a2489fe`](https://github.com/svange/openbrain/commit/a2489fe8cca37f5ee5d2bd52dda93c0f47ce0c84))

* Merge branch &#39;main&#39; of github.com:/svange/openbrain into fix/pipeline-not-releasing-on-master-only-on-refs

# Conflicts:
#	.github/workflows/semantic-branches.yml ([`32caec3`](https://github.com/svange/openbrain/commit/32caec39ae13a68466afd8dba13e6e6a8276c1b9))

* Fixing pipeline ([`cd99171`](https://github.com/svange/openbrain/commit/cd99171e612768b61c3d6f62d268393af2c4a6e8))

* bugfixing #pr ([`e4724b0`](https://github.com/svange/openbrain/commit/e4724b00f8fef5b7b9d889ed77cbf4f634e7a3fd))


## v0.4.10 (2023-09-23)

### Unknown

* AUTO-PR ci/fix/pipeline-not-releasing-on-master-only-on-refs -&gt; main (#28)

Merge pull request #28 ([`7b62ea6`](https://github.com/svange/openbrain/commit/7b62ea6c6ce7397bce3c047ce86c1d261798cb38))

* bugfixing #pr ([`355b97d`](https://github.com/svange/openbrain/commit/355b97d19ec47d87e8e7823599bddfb405f0a443))

* bugfixing #pr ([`d05b21c`](https://github.com/svange/openbrain/commit/d05b21c7554fefaaefae5f26179607220973ef48))

* Merge remote-tracking branch &#39;origin/fix/pipeline-not-releasing-on-master-only-on-refs&#39; into fix/pipeline-not-releasing-on-master-only-on-refs ([`f67756f`](https://github.com/svange/openbrain/commit/f67756f5282267f27bdd0b5f0c27a1e517953e55))

* bugfixing #pr ([`5afeaee`](https://github.com/svange/openbrain/commit/5afeaeee6dcdca8640fc3cf14e4de9c1f23042df))

* bugfixing ([`69fc1b9`](https://github.com/svange/openbrain/commit/69fc1b9bfc444b12574423c6e22854da57361c1e))

* Merge remote-tracking branch &#39;origin/fix/pipeline-not-releasing-on-master-only-on-refs&#39; into fix/pipeline-not-releasing-on-master-only-on-refs ([`5e29fd1`](https://github.com/svange/openbrain/commit/5e29fd1464ff9f85c25d350665c3b898d03e29c5))

* trying regex in pyproject.toml #pr ([`dd7c77a`](https://github.com/svange/openbrain/commit/dd7c77a1b11b4f444e2cca13f534d3dd50520a37))

* trying regex in pyproject.toml ([`e8056dd`](https://github.com/svange/openbrain/commit/e8056dd0ab8f6ed7e92f48b9f4b52f63c27f32f2))

* tweaked readme... and pipeline, sorry ([`56ad92c`](https://github.com/svange/openbrain/commit/56ad92cb60bb12ead0ed11fa1796474795a483ea))

* tweaked readme... sorry ([`a0391d4`](https://github.com/svange/openbrain/commit/a0391d4311f0c3b5834fb254322ec5ef7cd007ef))


## v0.4.9 (2023-09-23)

### Unknown

* fixing ob command and ci-cd bug that launches pre-commit job too often. ([`496bdfc`](https://github.com/svange/openbrain/commit/496bdfc0048443f934dad868a3f7436ffd33da44))

* Merge pull request #27

🤖📦🐍 style/update-readmes → main ([`e6cc5e7`](https://github.com/svange/openbrain/commit/e6cc5e7733b531dc6e6f405354c70b04b55dda1d))


## v0.4.8 (2023-09-23)

### Style

* style: #pr Merge branch &#39;main&#39; of github.com:/svange/openbrain into style/update-readmes

# Conflicts:
#	.github/PULL_REQUEST_TEMPLATE.md
#	CONTRIBUTING.md
#	README.md ([`da6ba8d`](https://github.com/svange/openbrain/commit/da6ba8def87592d0ea3c575b4af2f7d34d45aad7))

### Unknown

* Merge pull request #26

* integrated pre-commit

* enforce pre-commit at pr time

* update README.md and start enforcing code quality. ([`9588f32`](https://github.com/svange/openbrain/commit/9588f329c9a7c4a0d227b891dc1e0a50d58d6aec))

* Updated README.md and CONTRIBUTING.md. ([`c0cca05`](https://github.com/svange/openbrain/commit/c0cca053c27719adf389684a3ff793187f1f7fdc))

* integrated pre-commit with many hooks to help with code quality, added github action to enforce it #pr ([`10aa27e`](https://github.com/svange/openbrain/commit/10aa27e2ee0c3e1b3a5e1e87b3485908c1b89c81))

* update README.md and start enforcing code quality.
Added guard so that PRs aren&#39;t always submitted upon pushes to this branch. ([`97cd906`](https://github.com/svange/openbrain/commit/97cd906ba2e7b44b3d95571047ae5ee64f976a7c))

* Merge branch &#39;main&#39; of github.com:/svange/openbrain into style/enable-pre-commit

# Conflicts:
#	README.md ([`1230463`](https://github.com/svange/openbrain/commit/12304630491001dd4a40120801150127db5521e5))

* update README.md and start enforcing code quality. ([`2226f1b`](https://github.com/svange/openbrain/commit/2226f1bb7b95f4b33e23e508b78b19a20ac425e4))


## v0.4.7 (2023-09-22)

### Unknown

* Merge pull request #25

* Updating README badge

* re-enabling pipeline steps

* Merge branch &#39;main&#39; of github.com:/svange/openbrain into style/ci-cd-…

* re-enabling pipeline steps

* Merge branch &#39;main&#39; of github.com:/svange/openbrain into style/ci-cd-… ([`b52af2b`](https://github.com/svange/openbrain/commit/b52af2b47df6d4b616caef768404cc6d75210511))

* Merge branch &#39;main&#39; of github.com:/svange/openbrain into style/ci-cd-standup ([`c9a4796`](https://github.com/svange/openbrain/commit/c9a479656578089f7c5902c1f3b6d9b4428e388f))

* re-enabling pipeline steps ([`00f5839`](https://github.com/svange/openbrain/commit/00f583956c3be99cbaf2bcbeaee81c2bb81dab9b))


## v0.4.6 (2023-09-22)

### Unknown

* 🤖📦🐍 style/ci-cd-standup → main (#24)

* Updating README badge



* re-enabling pipeline steps ([`a23f325`](https://github.com/svange/openbrain/commit/a23f3258901ae8037c78f2505bd690f7e495764b))

* Merge branch &#39;main&#39; of github.com:/svange/openbrain into style/ci-cd-standup ([`11868ad`](https://github.com/svange/openbrain/commit/11868ade0dbd33116f38027ec440cab4a09c8b28))

* re-enabling pipeline steps ([`6381757`](https://github.com/svange/openbrain/commit/63817576ca9306f4d737c3ec0792b1448617d202))


## v0.4.5 (2023-09-22)

### Unknown

* Updating README badge (#23) ([`941f738`](https://github.com/svange/openbrain/commit/941f73832068275f7d8be81afc0ba90bf1b08436))

* Updating README badge ([`e74c885`](https://github.com/svange/openbrain/commit/e74c8851c23080d5aa8b2ed50594e68699b17c9a))

* Working CI/CD pipeline tested, but no tests on main branch commits yet. ([`7f643da`](https://github.com/svange/openbrain/commit/7f643da9da25205e7b17519e72884ba99654556e))


## v0.4.4 (2023-09-22)

### Unknown

* Working CI/CD pipeline tested, but no tests on main branch commits yet. ([`9366090`](https://github.com/svange/openbrain/commit/9366090fdd6402b664df67cf796de4387f51c3cb))


## v0.4.3 (2023-09-22)

### Unknown

* Working CI/CD pipeline tested, but no tests on main branch commits yet. ([`c4e8baa`](https://github.com/svange/openbrain/commit/c4e8baa5a384e6afded5536c5e4353ea329e1598))


## v0.4.2 (2023-09-22)

### Unknown

* Working CI/CD pipeline tested, but no tests on main branch commits yet. ([`32261d4`](https://github.com/svange/openbrain/commit/32261d4fe7fe1dd85d86d6847ecd241d66b13dc9))


## v0.4.1 (2023-09-22)

### Unknown

* Working CI/CD pipeline tested, but no tests on main branch commits yet. ([`67f6e97`](https://github.com/svange/openbrain/commit/67f6e97a41e8e7c2251f8ee6779dfc2fba300112))

* Working CI/CD pipeline tested, but no tests on main branch commits yet. ([`5663f0c`](https://github.com/svange/openbrain/commit/5663f0c2528152a0e93b60deb317e1f0d5ea8d8b))


## v0.4.0 (2023-09-22)

### Test

* test: Standing up CI/CD. ([`a1cddd1`](https://github.com/svange/openbrain/commit/a1cddd12eba3da6081aef946d1efa90c04c223ae))

### Unknown

* 🤖📦🐍 feat/ci-cd → main (#22)

Stood up first CI/CD pipeline for semantic versioning with github actions, and poetry. ([`742f797`](https://github.com/svange/openbrain/commit/742f79702045668dffde7c6ab6bf0f21a2623a2b))

* Standing up CI/CD ([`e804686`](https://github.com/svange/openbrain/commit/e804686552ba998d2ddfc9c97c2fa97e90f2eb87))

* Standing up CI/CD ([`69503b6`](https://github.com/svange/openbrain/commit/69503b6526cc8d78de91e678943579546386fbbf))

* Standing up CI/CD ([`621993f`](https://github.com/svange/openbrain/commit/621993f92196dd986f286004f78d1d2e09c84aca))

* Standing up CI/CD ([`6662ebe`](https://github.com/svange/openbrain/commit/6662ebe95cf6df9c9c99a5a97448b7ad71bebfed))

* Standing up CI/CD ([`d1ce2a7`](https://github.com/svange/openbrain/commit/d1ce2a75b66a7d803015654269aaad8968cea96e))

* Standing up CI/CD ([`c1e78e0`](https://github.com/svange/openbrain/commit/c1e78e0aa1aef05174e29b3cee7c8e4251868311))

* Standing up CI/CD ([`fdeebf7`](https://github.com/svange/openbrain/commit/fdeebf7030ea1e5017538d56c8c29f8e57e518d6))

* Standing up CI/CD ([`374ac46`](https://github.com/svange/openbrain/commit/374ac46c82be22f1e8693c15056a563084617969))

* Standing up CI/CD ([`07ea54d`](https://github.com/svange/openbrain/commit/07ea54d57e558d405e9f52493ef76186551a305f))

* Standing up CI/CD ([`54b6093`](https://github.com/svange/openbrain/commit/54b609385a64c33d3198b87ba6395f15384455cd))

* Standing up CI/CD ([`9be0be6`](https://github.com/svange/openbrain/commit/9be0be69a05bee1a15db760ad08f0f7e9108aaa3))

* Standing up CI/CD ([`aa79c00`](https://github.com/svange/openbrain/commit/aa79c00cd5046709b84643e657c5a27caa3451ea))

* Standing up CI/CD ([`6f465bd`](https://github.com/svange/openbrain/commit/6f465bdc956fe46a14874b9d6e4cf4331a9dba19))

* Standing up CI/CD ([`d6cf33e`](https://github.com/svange/openbrain/commit/d6cf33ea8c060e3461d7d96c36ed2ba0eca9c849))

* Standing up CI/CD ([`3c60a28`](https://github.com/svange/openbrain/commit/3c60a28926be9f625dd7d92ba71b922a8e6dc59c))

* Standing up CI/CD ([`e1890ed`](https://github.com/svange/openbrain/commit/e1890ed6519376c12843786a67aa142884e0df2c))

* Standing up CI/CD ([`2071551`](https://github.com/svange/openbrain/commit/2071551aac816d022dd12f61bf55dfd3709af35e))

* Standing up CI/CD ([`d6f212a`](https://github.com/svange/openbrain/commit/d6f212a055ec009910336174c9e47b535b093080))

* Standing up CI/CD ([`e74436a`](https://github.com/svange/openbrain/commit/e74436a91c572dfec185f77eafdda32b3fb5b4b7))

* Standing up CI/CD ([`3dc6bf4`](https://github.com/svange/openbrain/commit/3dc6bf49601c30a4f90ecc84d8f7455c471520d2))

* Standing up CI/CD ([`e14c464`](https://github.com/svange/openbrain/commit/e14c4648a1e8d795ba373fe63a44dd4ca039dd18))

* Standing up CI/CD ([`11db018`](https://github.com/svange/openbrain/commit/11db018483701a65dd70e4c32f60ff213efccd3d))

* Standing up CI/CD ([`752502b`](https://github.com/svange/openbrain/commit/752502b8a43bb3dd8b6134b67c469c91bedbf11d))

* Standing up CI/CD ([`63b1e9a`](https://github.com/svange/openbrain/commit/63b1e9a1c0c242260aa0c1abcf42b96f0926ae63))

* Standing up CI/CD ([`9d7a049`](https://github.com/svange/openbrain/commit/9d7a04928554db7198d31e38b9a78e1fe02be78c))

* Standing up CI/CD ([`df292ff`](https://github.com/svange/openbrain/commit/df292ff0468087c723c91525608823f61e7d9e08))

* Standing up CI/CD ([`e074459`](https://github.com/svange/openbrain/commit/e0744596885101accc7eca23ff922c44a1356fbc))

* Standing up CI/CD ([`fde0d5a`](https://github.com/svange/openbrain/commit/fde0d5a51a0edff9ed71d761331be1dbda114912))

* Standing up CI/CD ([`7eca82d`](https://github.com/svange/openbrain/commit/7eca82db0964847ce0ec47a8b70edbb4f63bbf85))

* Standing up CI/CD ([`d5e4f1b`](https://github.com/svange/openbrain/commit/d5e4f1bb196278dc3313d24e6e47d8f17dfd4470))

* Standing up CI/CD ([`f16074e`](https://github.com/svange/openbrain/commit/f16074e48a1987cc8e2263b6359e957f1b4b6427))

* Standing up CI/CD ([`00c3db0`](https://github.com/svange/openbrain/commit/00c3db07bccc41df7aa1363233659787e10318b7))

* Standing up CI/CD ([`0b89e6b`](https://github.com/svange/openbrain/commit/0b89e6b301960a9b75ecb4d47b483caeef8e5449))

* Standing up CI/CD ([`106b394`](https://github.com/svange/openbrain/commit/106b3945acf80b744a7e69ef0611de952111caed))

* Standing up CI/CD ([`cc288aa`](https://github.com/svange/openbrain/commit/cc288aab662ec194bc3adb0535e9204dcde36d61))

* Standing up CI/CD ([`b91d158`](https://github.com/svange/openbrain/commit/b91d1586489a76ebf792df3fa401e5e302a20d22))

* Standing up CI/CD ([`c3240f5`](https://github.com/svange/openbrain/commit/c3240f51bd127832b4a2dcce0b9354f0854ad122))

* Standing up CI/CD ([`f0e748e`](https://github.com/svange/openbrain/commit/f0e748e5aeaef1f6f391c656a5ca2b79da6587a5))

* Standing up CI/CD ([`b7190c8`](https://github.com/svange/openbrain/commit/b7190c8f792c02a7d1bb1133892528474bd9b5cb))

* Standing up CI/CD ([`d22270f`](https://github.com/svange/openbrain/commit/d22270f7cc05a1c0876c89b5e74dd08d0de9d121))

* Standing up CI/CD ([`5e7ea9e`](https://github.com/svange/openbrain/commit/5e7ea9e80aaa6ac79bbff4999d3684e7e93e47be))

* Standing up CI/CD ([`f9fd71d`](https://github.com/svange/openbrain/commit/f9fd71d353bd74a44d270937f998b453f04b9d9a))

* Standing up CI/CD ([`1b9b107`](https://github.com/svange/openbrain/commit/1b9b107b9971a8ce7db82c7f65b7034fa73dbeef))

* Standing up CI/CD ([`f657e00`](https://github.com/svange/openbrain/commit/f657e00e4cf2e44a0a1f6df9f149690515a70dea))

* Standing up CI/CD ([`d54f69d`](https://github.com/svange/openbrain/commit/d54f69d9923523661ade1d93f6251447cefa6cac))

* Standing up CI/CD ([`7df428c`](https://github.com/svange/openbrain/commit/7df428c0b6645b7c597cd6b03998c26fa9480ca9))

* Standing up CI/CD ([`58ef92c`](https://github.com/svange/openbrain/commit/58ef92c422810cb89c4010efa25f6622800398a9))

* Standing up CI/CD ([`1b2caf1`](https://github.com/svange/openbrain/commit/1b2caf1ad949bf49dd467467eac99a21b0fb2a33))

* Standing up CI/CD ([`969a9cd`](https://github.com/svange/openbrain/commit/969a9cd0b04f84fbf2d61dd44bfe7cb7ef408006))

* Standing up CI/CD ([`3e744a3`](https://github.com/svange/openbrain/commit/3e744a30910e30cc3f8735c3d5553fab7be83afb))

* Standing up CI/CD ([`ca19b41`](https://github.com/svange/openbrain/commit/ca19b41b03345ddbf2444561c422eeb17fe534ad))

* Standing up CI/CD ([`3d463c1`](https://github.com/svange/openbrain/commit/3d463c1eae9dd3f0d0d018f57503cf7ce627673d))

* Standing up CI/CD ([`b641e7d`](https://github.com/svange/openbrain/commit/b641e7d690022859f73e6d558d4ba675e1b4051c))

* Standing up CI/CD ([`fca045b`](https://github.com/svange/openbrain/commit/fca045b11b132d883192215da99b038a6ec014ab))

* Standing up CI/CD ([`f8cf346`](https://github.com/svange/openbrain/commit/f8cf346c4754560cbbb2e8db86f62ea24a158e42))

* Standing up CI/CD ([`06e18ba`](https://github.com/svange/openbrain/commit/06e18bab9a08f33930cc47fb490c3b9d09d73ae3))

* Merge branch &#39;features/cicd-pipeline&#39; of github.com:/svange/openbrain into dev ([`26b1c68`](https://github.com/svange/openbrain/commit/26b1c68c383c4070056fcf8211a20e7260daf86e))

* Standing up CI/CD ([`f30c329`](https://github.com/svange/openbrain/commit/f30c32937f7e544a591ada2b08dfc127ccf6592d))

* Standing up CI/CD ([`887752f`](https://github.com/svange/openbrain/commit/887752fc5998e409283205d5bc9afd0bb8a41e95))

* tweaking ([`ed74c90`](https://github.com/svange/openbrain/commit/ed74c902f452b0c0dc958af9f786bcaccc60c9c6))

* tweaking ([`55dd6ba`](https://github.com/svange/openbrain/commit/55dd6bae52c56e8a0d700f8d27f91eab909d4cc0))

* tweaking ([`f30d3bd`](https://github.com/svange/openbrain/commit/f30d3bd78568bb31d97f8a69f5c2fd3ae08b0f92))


## v0.2.12 (2023-09-22)

### Unknown

* tweaking ([`55b60dc`](https://github.com/svange/openbrain/commit/55b60dcca8f75f8d7993bf7dd2c820f97a6f63de))


## v0.2.11 (2023-09-22)

### Unknown

* removed smever in an attempt to make github play along. ([`f4d651f`](https://github.com/svange/openbrain/commit/f4d651f37451f8ea775432cbde5d47cfc8d0f3ba))


## v0.2.10 (2023-09-22)

### Unknown

* removed smever in an attempt to make github play along. ([`d589fc7`](https://github.com/svange/openbrain/commit/d589fc73aa316c15e223a7225e762224080621da))


## v0.2.9 (2023-09-22)

### Unknown

* updated dependencies ([`996a12b`](https://github.com/svange/openbrain/commit/996a12b2e44dbb160fda6352172c0b1cdabb5070))


## v0.2.7 (2023-09-22)

### Unknown

* updated dependencies ([`27d3a7b`](https://github.com/svange/openbrain/commit/27d3a7beb276246009f1a43fa5d4c286234eab95))


## v0.2.6 (2023-09-22)

### Unknown

* updated dependencies ([`21e50c5`](https://github.com/svange/openbrain/commit/21e50c59bf11a728b8ef8aabe4b10d3e0a74009b))


## v0.2.5 (2023-09-22)

### Unknown

* updated CONTRIBUTING.md ([`dd0b5a2`](https://github.com/svange/openbrain/commit/dd0b5a27d5755fd91f810a6f9e040c3790decd90))


## v0.2.4 (2023-09-22)

### Unknown

* updated CI/CD pipeline ([`d4800ed`](https://github.com/svange/openbrain/commit/d4800edd5220a453d9ebc28ab505b38dc692b829))

* Merge remote-tracking branch &#39;origin/dev&#39; into dev ([`51c3427`](https://github.com/svange/openbrain/commit/51c3427f4dea191d9f579851fd321aec1ce3e16d))

* Merge remote-tracking branch &#39;origin/dev&#39; into dev ([`3e618f2`](https://github.com/svange/openbrain/commit/3e618f291c280cce7b3c7e5a065c3610526dd48e))

* Merge remote-tracking branch &#39;origin/dev&#39; into dev ([`f8e76a2`](https://github.com/svange/openbrain/commit/f8e76a2bec3d59bdfe34308093a389db6b0874f1))

* Setting up CI/CD pipeline and workflow ([`494e23d`](https://github.com/svange/openbrain/commit/494e23dbea902c301e691b45c58e3184d578a53e))

* Setting up CI/CD pipeline and workflow ([`f9ef366`](https://github.com/svange/openbrain/commit/f9ef366174de6884718400c8040923d70dae084b))


## v0.2.0 (2023-09-22)

### Unknown

* Setting up CI/CD pipeline and workflow ([`c779436`](https://github.com/svange/openbrain/commit/c779436f7e4032a2725a5348c17b08ef3f4f7041))

* Setting up CI/CD pipeline and workflow ([`951c908`](https://github.com/svange/openbrain/commit/951c9085caab1eac3f9137f3bb8d47be00ef5607))

* Setting up CI/CD pipeline and workflow ([`0f41845`](https://github.com/svange/openbrain/commit/0f41845682b92ad8495da0be2030b8db8da63f45))

* Setting up CI/CD pipeline and workflow ([`1c2a8aa`](https://github.com/svange/openbrain/commit/1c2a8aa28f3733578d5760272654ab911267727f))

* Merge remote-tracking branch &#39;origin/dev&#39; into dev ([`d8050fa`](https://github.com/svange/openbrain/commit/d8050fa9ee898207197bb049376bb7f74a325dbf))

* Setting up CI/CD pipeline and workflow ([`cbde9ba`](https://github.com/svange/openbrain/commit/cbde9baaf63d6a7c88e69003c53d0221ff221cdc))

* Setting up CI/CD pipeline and workflow ([`48b6978`](https://github.com/svange/openbrain/commit/48b69786436591da4c406d20482a072e1b78fbe7))

* Updated README.md ([`0808e6a`](https://github.com/svange/openbrain/commit/0808e6a287ff8a8ad0f2f0c906499b603b66458f))

* Merge branch &#39;main&#39; of github.com:/svange/openbrain into dev

# Conflicts:
#	.aws-sam/build/template.yaml
#	.env.example
#	.github/workflows/main-publish.yaml
#	LICENSE.md
#	README.md
#	ci_cd.py
#	pyproject.toml
#	template.yaml ([`9b0aad0`](https://github.com/svange/openbrain/commit/9b0aad0a8b922a9d924bb432e5262f0b2bada93d))

* Updated README.md ([`2ff9ccc`](https://github.com/svange/openbrain/commit/2ff9ccc953ae8cd3004ac5224281764862065144))

* Version bump to fix failed deploy ([`290ce13`](https://github.com/svange/openbrain/commit/290ce13f176e6a188745b7bacfe736278766b78f))

* Establishing project structure, publishing, license and other metadata details. ([`2c2c779`](https://github.com/svange/openbrain/commit/2c2c7797a51632a8ce2f97c16206ba2200d921a9))

* initial commit ([`4fb4d38`](https://github.com/svange/openbrain/commit/4fb4d380eeb2841133c8d151901085cb9f009197))

* added auto version bumping ([`0951f7f`](https://github.com/svange/openbrain/commit/0951f7fd7628200c6d4fa80e8c30760a7174a83b))

* troubleshooting ci/cd pipeline ([`19a2053`](https://github.com/svange/openbrain/commit/19a2053626899e2dab18f7ec7c569c5eeaa4c3fa))

* troubleshooting ci/cd pipeline ([`7d20728`](https://github.com/svange/openbrain/commit/7d207284db79834a114961636b4c7328da0e6b4c))

* troubleshooting ci/cd pipeline ([`7778547`](https://github.com/svange/openbrain/commit/7778547a4a89ff52926c68054930b171e8008d1d))

* troubleshooting ci/cd pipeline ([`c5fd255`](https://github.com/svange/openbrain/commit/c5fd2559a474f79344266147569cdabad87d7a0b))

* troubleshooting ci/cd pipeline ([`b8cf544`](https://github.com/svange/openbrain/commit/b8cf54419016be525ea3fe4f036c5272b244a8c9))

* Merge remote-tracking branch &#39;origin/dev&#39; into dev ([`5afb255`](https://github.com/svange/openbrain/commit/5afb2555e8cf85ac1470aa9f524d9b0592348315))

* troubleshooting ci/cd pipeline ([`c221f35`](https://github.com/svange/openbrain/commit/c221f3523e9ffc98c96cb531e9ad49f8145aa5ea))

* troubleshooting ci/cd pipeline ([`ca73a78`](https://github.com/svange/openbrain/commit/ca73a7841345f7bc03d7d75b4ee31979bdf0a3dd))

* Merge remote-tracking branch &#39;origin/dev&#39; into dev ([`e6990ed`](https://github.com/svange/openbrain/commit/e6990ed016b2edf742ccfcfc33b00fab966a0116))

* initial commit ([`9626530`](https://github.com/svange/openbrain/commit/96265303eb71cdb1e30d39346b883b21041b1ce0))

* initial commit ([`9c8c944`](https://github.com/svange/openbrain/commit/9c8c94400152a7b2b41e7190196387908bb0097f))

* initial commit ([`9e7ea40`](https://github.com/svange/openbrain/commit/9e7ea403a357a8bb9563c077e134dbdf7ab31fae))

* initial commit ([`b8bdfce`](https://github.com/svange/openbrain/commit/b8bdfce01a57ce5d4f96d877892a50df3d590f2d))

* Initial commit ([`8bb71cc`](https://github.com/svange/openbrain/commit/8bb71cc4fba6a357f41e110e5d3b23f01def39ac))
