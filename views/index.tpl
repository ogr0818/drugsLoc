<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>住院儲位</title>
  <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
  <main class="page-shell">
    <section class="card">
      <form method="post" class="query-row" autocomplete="off" action="/">
      <label class="bar-cord">藥品代碼：
        <input
          type="text"
          name="code"
          value="{{code}}"
          class="code-input"
          placeholder="請輸入藥品代碼"
          autofocus
        >
        <button type="submit" class="submit-btn">查詢</button>
      </label>
      </form>

      <div class="status-row">
        % if message:
          <div class="status-box error">{{message}}</div>
        % elif result:
          <div class="status-box success">商品名： {{result['drug_name']}} ｜ 儲位： {{result['location']}}</div>
        % else:
          <div class="status-box neutral">資料來源：{{source_name}}</div>
        % end
      </div>

      <div class="map-wrap">
        % for row_no in range(6, 0, -1):
          <div class="map-row map-row-8">
            % for col_no in range(8, 0, -1):
              % location = f'{col_no}-{row_no}'
              <div class="slot {{'active' if active_location == location else ''}}">{{location}}</div>
            % end
          </div>
        % end
        <div class="front-rack {{'active' if active_location == '層架' else ''}}">層架</div>
      </div>
    </section>
  </main>
</body>
</html>
