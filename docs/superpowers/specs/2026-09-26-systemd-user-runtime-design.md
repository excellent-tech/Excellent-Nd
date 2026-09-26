# systemd user runtime design

Linux execution host では、repository ごとの runtime を `excellent-nd@<instance>.service` として常駐させる。template unit は全 instance で共有し、host-local mapping を `$XDG_CONFIG_HOME/excellent-nd/instances/<instance>.json` に置く。mapping は repository、repository root、WORKFLOW、Symphony、repository config、observer の絶対 path と実行引数だけを持ち、credential は持たない。

service entrypoint は mapping と path の整合を fail-closed で検証し、起動時に `gh auth token` を取得して child process の `GITHUB_TOKEN` にだけ設定した後、既存 `runtime_observer.py run` を `exec` する。Codex は同一 user の既存認証を使う。unit は `Restart=always` とし、log は user journal に送る。

`setup.py --start` は Linux で unit/mapping を install/updateし、`daemon-reload`、enable、restart、active と observer/Symphony process tree の確認まで行う。診断用 foreground は `--foreground` に分離する。unsupported platform、unsafe instance、既存 instance と別 repository の衝突、inactive/process 不在は失敗にする。basename を既定 instance とし、衝突時だけ `--service-instance` で明示的に回避する。

実 systemd を使わない unit test で rendering、mapping、collision、secret 非混入、CLI 分岐を検証し、実 host では2 repositoryを個別 serviceとして起動して preflight と pickup evidence を確認する。public artifact の例は `example-org/sample-app`、`sample-app`、`<repository-instance>` のみにする。
