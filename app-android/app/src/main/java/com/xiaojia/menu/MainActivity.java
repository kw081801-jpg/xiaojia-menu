package com.xiaojia.menu;

import android.annotation.SuppressLint;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.MotionEvent;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import org.json.JSONObject;
import androidx.core.content.FileProvider;
import android.webkit.WebViewClient;
import android.widget.Toast;

public class MainActivity extends android.app.Activity {
    private static final String BASE = "http://101.43.45.186:8080/";
    private static final String ADMIN = BASE + "admin.html";

    private WebView web;
    private long lastLoad = 0;
    private float downY = 0;
    private boolean pulling = false;
    private boolean menuShown = false;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private Runnable pressTask = null;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        web = new WebView(this);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setSupportZoom(false);
        s.setMediaPlaybackRequiresUserGesture(false);

        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, true);

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if (url.startsWith("http://") || url.startsWith("https://")) {
                    view.loadUrl(url);
                    return true;
                }
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
                } catch (Exception ignored) { }
                return true;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                lastLoad = System.currentTimeMillis();
            }
        });
        web.setWebChromeClient(new WebChromeClient());


        // 下拉到顶再往下拉 200px：刷新；按住 1.6 秒：菜单
        web.setOnTouchListener(new View.OnTouchListener() {
            @Override
            public boolean onTouch(View v, MotionEvent e) {
                switch (e.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        downY = e.getY();
                        pulling = (web.getScrollY() == 0);
                        menuShown = false;
                        if (pressTask != null) handler.removeCallbacks(pressTask);
                        pressTask = new Runnable() {
                            @Override
                            public void run() {
                                menuShown = true;
                                showMenu();
                            }
                        };
                        handler.postDelayed(pressTask, 1600);
                        break;
                    case MotionEvent.ACTION_MOVE:
                        if (Math.abs(e.getY() - downY) > 24 && pressTask != null) {
                            handler.removeCallbacks(pressTask);
                        }
                        break;
                    case MotionEvent.ACTION_UP:
                    case MotionEvent.ACTION_CANCEL:
                        if (pressTask != null) handler.removeCallbacks(pressTask);
                        if (!menuShown && pulling && e.getY() - downY > 220) {
                            web.reload();
                            Toast.makeText(MainActivity.this, "已刷新", Toast.LENGTH_SHORT).show();
                        }
                        pulling = false;
                        break;
                }
                return false;
            }
        });

        web.loadUrl(BASE);
        checkUpdate();
    }

    // ---------- 检查并安装最新版 ----------
    private void checkUpdate() {
        new Thread(() -> {
            try {
                HttpURLConnection c = (HttpURLConnection) new URL(BASE + "app/version.json").openConnection();
                c.setConnectTimeout(6000);
                c.setReadTimeout(6000);
                c.setRequestProperty("Cache-Control", "no-cache");
                InputStream in = c.getInputStream();
                byte[] buf = new byte[8192];
                StringBuilder sb = new StringBuilder();
                int n;
                while ((n = in.read(buf)) > 0) sb.append(new String(buf, 0, n, "UTF-8"));
                in.close();
                JSONObject o = new JSONObject(sb.toString());
                final int remoteCode = o.optInt("versionCode", 0);
                final String remoteName = o.optString("versionName", "");
                final String apkUrl = o.optString("url", "");
                final String notes = o.optString("notes", "");
                if (remoteCode > BuildConfig.VERSION_CODE && apkUrl.length() > 0) {
                    runOnUiThread(() -> new AlertDialog.Builder(MainActivity.this)
                            .setTitle("发现新版本 " + remoteName)
                            .setMessage(notes.length() > 0 ? notes : "是否下载并安装？")
                            .setPositiveButton("下载安装", (d, w) -> downloadApk(apkUrl, remoteName))
                            .setNegativeButton("以后再说", null)
                            .show());
                }
            } catch (Exception ignored) { }
        }).start();
    }

    private void downloadApk(String urlStr, String ver) {
        Toast.makeText(this, "开始下载 " + ver, Toast.LENGTH_SHORT).show();
        new Thread(() -> {
            try {
                File apk = new File(getCacheDir(), "update.apk");
                HttpURLConnection c = (HttpURLConnection) new URL(urlStr).openConnection();
                c.setConnectTimeout(10000);
                c.setReadTimeout(60000);
                try (InputStream in = c.getInputStream();
                     FileOutputStream out = new FileOutputStream(apk)) {
                    byte[] buf = new byte[16384];
                    int n;
                    while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
                }
                runOnUiThread(() -> installApk(apk));
            } catch (Exception e) {
                runOnUiThread(() -> Toast.makeText(this, "下载失败：" + e.getMessage(), Toast.LENGTH_LONG).show());
            }
        }).start();
    }

    private void installApk(File apk) {
        try {
            android.net.Uri uri = FileProvider.getUriForFile(this, "com.xiaojia.menu.fileprovider", apk);
            Intent i = new Intent(Intent.ACTION_VIEW);
            i.setDataAndType(uri, "application/vnd.android.package-archive");
            i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(i);
        } catch (Exception e) {
            Toast.makeText(this, "启动安装失败：" + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private void showMenu() {
        android.view.View v = getLayoutInflater().inflate(R.layout.dialog_menu, null);
        AlertDialog dlg = new AlertDialog.Builder(this).setView(v).create();
        if (dlg.getWindow() != null) {
            dlg.getWindow().setBackgroundDrawableResource(android.R.color.transparent);
        }
        v.findViewById(R.id.btnRefresh).setOnClickListener(x -> { web.reload(); dlg.dismiss(); });
        v.findViewById(R.id.btnAdmin).setOnClickListener(x -> { web.loadUrl(ADMIN); dlg.dismiss(); });
        v.findViewById(R.id.btnCancel).setOnClickListener(x -> dlg.dismiss());
        dlg.show();
    }

    @Override
    protected void onResume() {
        super.onResume();
        // 从后台切回来超过 1 分钟就自动刷新，避免上传图片回来页面被重置
        if (web != null && lastLoad > 0 && System.currentTimeMillis() - lastLoad > 60000) {
            web.reload();
        }
    }

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
