# 17 条最终对照代码

本目录从现有文件逐字节复制，不重新生成或改写测试。

- 15 条 AI 修复候选：TC_001、TC_005、TC_006、TC_010、TC_012、TC_013、TC_014、TC_015、TC_017、TC_018、TC_019、TC_022、TC_023、TC_025、TC_026。
- TC_007：来自 `runs/manual_patch_TC_007/after.py` 的补丁版本，不能据此确认由 AI 修复。
- TC_028：未找到独立 AI 修复候选，保留工作目录中未修改的 AI 原始版本。

`sources.json` 记录每条代码的原路径、版本类别和 SHA-256。原路径中的 `runs/` 是本地来源记录，不随源码提交。首次生成版位于 `baselines/raw_initial/`，对应手工版位于 `manual_tests/`。

本目录是对照存档；执行与修复工具使用 `generated_tests/case_raw/`。
