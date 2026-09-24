# execution_target 与执行主机台账

本文定义一个仓库如何管理 0..N 台 Excellent-Nd 执行主机，包括注册、停用、删除和重新注册。

## 1. 主机何时算注册完成

注册分为两个阶段。

1. **生成本地注册候选**  
   `scripts/setup.py` 先检查前提条件、GitHub 认证、Symphony checksum、Codex 兼容性、WORKFLOW 和路由标签。只有冒烟验证通过后，才创建或更新 `.excellent-nd/targets/<target-id>.json`。
2. **发布共享注册**  
   检查生成的target文件，commit / push，并合并到运行分支（通常为main）。从此时起，ChatGPT、人工和其他执行主机都能通过GitHub读取同一份台账。

setup不会自动commit/push。 `enabled: true` 表示该主机已配置并可作为任务分配候选，不表示实时online heartbeat。

## 2. 注册第一台主机

在仓库根目录运行:

```bash
python3 scripts/setup.py \
  --repo OWNER/REPOSITORY \
  --repo-path . \
  --prefix .excellent-nd \
  --skill-confirmed
```

默认target ID为本机hostname。如果不希望把hostname写入Git，可显式指定alias。

冒烟验证PASS后，检查并commit `.excellent-nd/targets/<target-id>.json`。有branch protection时通过PR合并；Git变更被接受后才算共享注册完成。

## 3. 注册第2台及更多主机

在每台主机上执行相同setup。台账采用一台主机一个文件:

```text
.excellent-nd/targets/
├─ worker-a.json
├─ worker-b.json
└─ worker-c.json
```

每个Symphony profile同时要求 `symphony-ready` 和自己的 `nd-target:<id>`。只有target匹配的主机才会取得Issue。

不保存固定主机数量。注册数由文件数动态取得，新任务候选仅使用 `enabled: true` 的record。

```bash
python3 scripts/target_inventory.py list --repo-root .
```

## 4. 临时停用主机

不要直接删除台账文件。

1. 把 `enabled` 改为 `false`。
2. commit / push / merge，使ChatGPT不再把新Task分配给该主机。
3. 检查以该target为目标的open Issue。
4. 完成、阻塞，或通过带checkpoint的后继Issue迁移未完成任务。
5. 按需要停止Symphony profile/runtime。

不得修改现有Issue的 `execution_target`。迁移到其他主机时创建后继Issue。

## 5. 删除主机

采用 **disable -> drain -> delete**。

1. 先发布 `enabled: false`。
2. 确认该target没有active Task。
3. 停止该主机runtime/profile。
4. 删除并commit target record:

```bash
git rm .excellent-nd/targets/worker-b.json
git commit -m "ops: remove Excellent-Nd target worker-b"
git push
```

5. 有branch protection时通过PR合并。
6. 确认审计/回滚要求后，可按需删除host-local runtime state。

默认保留 `nd-target:<id>` GitHub label，使历史Issue仍易于理解。只有明确执行cleanup时才删除label。

## 6. 重新注册或改名

同一target重新注册时，再次运行setup，冒烟验证PASS后review并commit重新生成的record。

如果target identity本身变化，先注册新target，再停用旧target，通过带checkpoint的后继Issue迁移未完成工作，最后删除旧record。不要改写现有Issue上的target。

## 7. 台账数据

只保存非credential的路由/能力metadata，例如target ID、hostname、enabled、并发能力、验证时间和routing label。禁止保存token、password、API key、private key或credential。

## 8. ChatGPT分配规则

ChatGPT不假设固定机器数量。读取 `.excellent-nd/targets/*.json`，新任务只使用 `enabled: true` 的record；只有1台时可作为default candidate，多台时在Plan中按负载、依赖和用户指示分配。候选为0台时保持Task不可dispatch。
