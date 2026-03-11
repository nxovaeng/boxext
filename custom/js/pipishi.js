// Native QuickJS TVBox Spider for PiPiShi (皮皮狮)
// Author: Antigravity
// Description: Pure JS Spider using modern ES Module export (export default) for TVBox/ok影视

var $cfg = {
    name: "皮皮狮原生JS",
    type: 3,
    ext: "",
    searchable: 1,
    quickSearch: 1,
    filterable: 0
};

const siteUrl = "https://www.pipishi.fun";
let globalCookie = "";

const siteHeaders = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
};

// -------------------------------------------------------------
// MAC CMS DECODER (Reimplemented cleanly)
// -------------------------------------------------------------
var Decode1 = (function () {
    var exports = {};
    exports.get = function (url) {
        if (!url) return "";
        let decoded = "";
        try {
            if (typeof atob !== 'undefined') {
                decoded = atob(url);
            } else if (typeof Packages !== 'undefined' && Packages.android && Packages.android.util.Base64) {
                let bytes = Packages.android.util.Base64.decode(url, 0);
                decoded = new java.lang.String(bytes, "UTF-8");
            }
            return decoded;
        } catch (e) {
            return url;
        }
    };
    return exports;
})();

function PIPISHI_DECODE(url) {
    if (!url) return "";
    let decoded = Decode1.get(url);
    if (decoded && decoded.indexOf("http") === -1) {
        return url;
    }
    return decoded;
}

// -------------------------------------------------------------
// ANTI-BOT BYPASS (QuickJS Compatible base64 & MD5)
// -------------------------------------------------------------

function base64encode(str) {
    if (typeof btoa !== 'undefined') {
        return btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, function (match, p1) {
            return String.fromCharCode('0x' + p1);
        }));
    } else if (typeof Packages !== 'undefined') {
        let bytes = new java.lang.String(str).getBytes("UTF-8");
        return Packages.android.util.Base64.encodeToString(bytes, 2);
    }
    return "";
}

// Pure JS MD5 Polyfill for TVBox engines
function md5(string) {
    function md5_RotateLeft(lValue, iShiftBits) {
        return (lValue << iShiftBits) | (lValue >>> (32 - iShiftBits));
    }
    function md5_AddUnsigned(lX, lY) {
        var lX4, lY4, lX8, lY8, lResult;
        lX8 = (lX & 0x80000000); lY8 = (lY & 0x80000000);
        lX4 = (lX & 0x40000000); lY4 = (lY & 0x40000000);
        lResult = (lX & 0x3FFFFFFF) + (lY & 0x3FFFFFFF);
        if (lX4 & lY4) { return (lResult ^ 0x80000000 ^ lX8 ^ lY8); }
        if (lX4 | lY4) {
            if (lResult & 0x40000000) { return (lResult ^ 0xC0000000 ^ lX8 ^ lY8); }
            else { return (lResult ^ 0x40000000 ^ lX8 ^ lY8); }
        } else { return (lResult ^ lX8 ^ lY8); }
    }
    function md5_F(x, y, z) { return (x & y) | ((~x) & z); }
    function md5_G(x, y, z) { return (x & z) | (y & (~z)); }
    function md5_H(x, y, z) { return (x ^ y ^ z); }
    function md5_I(x, y, z) { return (y ^ (x | (~z))); }
    function md5_FF(a, b, c, d, x, s, ac) {
        a = md5_AddUnsigned(a, md5_AddUnsigned(md5_AddUnsigned(md5_F(b, c, d), x), ac));
        return md5_AddUnsigned(md5_RotateLeft(a, s), b);
    };
    function md5_GG(a, b, c, d, x, s, ac) {
        a = md5_AddUnsigned(a, md5_AddUnsigned(md5_AddUnsigned(md5_G(b, c, d), x), ac));
        return md5_AddUnsigned(md5_RotateLeft(a, s), b);
    };
    function md5_HH(a, b, c, d, x, s, ac) {
        a = md5_AddUnsigned(a, md5_AddUnsigned(md5_AddUnsigned(md5_H(b, c, d), x), ac));
        return md5_AddUnsigned(md5_RotateLeft(a, s), b);
    };
    function md5_II(a, b, c, d, x, s, ac) {
        a = md5_AddUnsigned(a, md5_AddUnsigned(md5_AddUnsigned(md5_I(b, c, d), x), ac));
        return md5_AddUnsigned(md5_RotateLeft(a, s), b);
    };
    function md5_ConvertToWordArray(string) {
        var lWordCount;
        var lMessageLength = string.length;
        var lNumberOfWords_temp1 = lMessageLength + 8;
        var lNumberOfWords_temp2 = (lNumberOfWords_temp1 - (lNumberOfWords_temp1 % 64)) / 64;
        var lNumberOfWords = (lNumberOfWords_temp2 + 1) * 16;
        var lWordArray = Array(lNumberOfWords - 1);
        var lBytePosition = 0;
        var lByteCount = 0;
        while (lByteCount < lMessageLength) {
            lWordCount = (lByteCount - (lByteCount % 4)) / 4;
            lBytePosition = (lByteCount % 4) * 8;
            lWordArray[lWordCount] = (lWordArray[lWordCount] | (string.charCodeAt(lByteCount) << lBytePosition));
            lByteCount++;
        }
        lWordCount = (lByteCount - (lByteCount % 4)) / 4;
        lBytePosition = (lByteCount % 4) * 8;
        lWordArray[lWordCount] = lWordArray[lWordCount] | (0x80 << lBytePosition);
        lWordArray[lNumberOfWords - 2] = lMessageLength << 3;
        lWordArray[lNumberOfWords - 1] = lMessageLength >>> 29;
        return lWordArray;
    };
    function md5_WordToHex(lValue) {
        var WordToHexValue = "", WordToHexValue_temp = "", lByte, lCount;
        for (lCount = 0; lCount <= 3; lCount++) {
            lByte = (lValue >>> (lCount * 8)) & 255;
            WordToHexValue_temp = "0" + lByte.toString(16);
            WordToHexValue = WordToHexValue + WordToHexValue_temp.substr(WordToHexValue_temp.length - 2, 2);
        }
        return WordToHexValue;
    };
    function md5_Utf8Encode(string) {
        string = string.replace(/\r\n/g, "\n");
        var utftext = "";
        for (var n = 0; n < string.length; n++) {
            var c = string.charCodeAt(n);
            if (c < 128) {
                utftext += String.fromCharCode(c);
            } else if ((c > 127) && (c < 2048)) {
                utftext += String.fromCharCode((c >> 6) | 192);
                utftext += String.fromCharCode((c & 63) | 128);
            } else {
                utftext += String.fromCharCode((c >> 12) | 224);
                utftext += String.fromCharCode(((c >> 6) & 63) | 128);
                utftext += String.fromCharCode((c & 63) | 128);
            }
        }
        return utftext;
    };
    var x = Array();
    var k, AA, BB, CC, DD, a, b, c, d;
    var S11 = 7, S12 = 12, S13 = 17, S14 = 22;
    var S21 = 5, S22 = 9, S23 = 14, S24 = 20;
    var S31 = 4, S32 = 11, S33 = 16, S34 = 23;
    var S41 = 6, S42 = 10, S43 = 15, S44 = 21;
    string = md5_Utf8Encode(string);
    x = md5_ConvertToWordArray(string);
    a = 0x67452301; b = 0xEFCDAB89; c = 0x98BADCFE; d = 0x10325476;
    for (k = 0; k < x.length; k += 16) {
        AA = a; BB = b; CC = c; DD = d;
        a = md5_FF(a, b, c, d, x[k + 0], S11, 0xD76AA478);
        d = md5_FF(d, a, b, c, x[k + 1], S12, 0xE8C7B756);
        c = md5_FF(c, d, a, b, x[k + 2], S13, 0x242070DB);
        b = md5_FF(b, c, d, a, x[k + 3], S14, 0xC1BDCEEE);
        a = md5_FF(a, b, c, d, x[k + 4], S11, 0xF57C0FAF);
        d = md5_FF(d, a, b, c, x[k + 5], S12, 0x4787C62A);
        c = md5_FF(c, d, a, b, x[k + 6], S13, 0xA8304613);
        b = md5_FF(b, c, d, a, x[k + 7], S14, 0xFD469501);
        a = md5_FF(a, b, c, d, x[k + 8], S11, 0x698098D8);
        d = md5_FF(d, a, b, c, x[k + 9], S12, 0x8B44F7AF);
        c = md5_FF(c, d, a, b, x[k + 10], S13, 0xFFFF5BB1);
        b = md5_FF(b, c, d, a, x[k + 11], S14, 0x895CD7BE);
        a = md5_FF(a, b, c, d, x[k + 12], S11, 0x6B901122);
        d = md5_FF(d, a, b, c, x[k + 13], S12, 0xFD987193);
        c = md5_FF(c, d, a, b, x[k + 14], S13, 0xA679438E);
        b = md5_FF(b, c, d, a, x[k + 15], S14, 0x49B40821);
        a = md5_GG(a, b, c, d, x[k + 1], S21, 0xF61E2562);
        d = md5_GG(d, a, b, c, x[k + 6], S22, 0xC040B340);
        c = md5_GG(c, d, a, b, x[k + 11], S23, 0x265E5A51);
        b = md5_GG(b, c, d, a, x[k + 0], S24, 0xE9B6C7AA);
        a = md5_GG(a, b, c, d, x[k + 5], S21, 0xD62F105D);
        d = md5_GG(d, a, b, c, x[k + 10], S22, 0x2441453);
        c = md5_GG(c, d, a, b, x[k + 15], S23, 0xD8A1E681);
        b = md5_GG(b, c, d, a, x[k + 4], S24, 0xE7D3FBC8);
        a = md5_GG(a, b, c, d, x[k + 9], S21, 0x21E1CDE6);
        d = md5_GG(d, a, b, c, x[k + 14], S22, 0xC33707D6);
        c = md5_GG(c, d, a, b, x[k + 3], S23, 0xF4D50D87);
        b = md5_GG(b, c, d, a, x[k + 8], S24, 0x455A14ED);
        a = md5_GG(a, b, c, d, x[k + 13], S21, 0xA9E3E905);
        d = md5_GG(d, a, b, c, x[k + 2], S22, 0xFCEFA3F8);
        c = md5_GG(c, d, a, b, x[k + 7], S23, 0x676F02D9);
        b = md5_GG(b, c, d, a, x[k + 12], S24, 0x8D2A4C8A);
        a = md5_HH(a, b, c, d, x[k + 5], S31, 0xFFFA3942);
        d = md5_HH(d, a, b, c, x[k + 8], S32, 0x8771F681);
        c = md5_HH(c, d, a, b, x[k + 11], S33, 0x6D9D6122);
        b = md5_HH(b, c, d, a, x[k + 14], S34, 0xFDE5380C);
        a = md5_HH(a, b, c, d, x[k + 1], S31, 0xA4BEEA44);
        d = md5_HH(d, a, b, c, x[k + 4], S32, 0x4BDECFA9);
        c = md5_HH(c, d, a, b, x[k + 7], S33, 0xF6BB4B60);
        b = md5_HH(b, c, d, a, x[k + 10], S34, 0xBEBFBC70);
        a = md5_HH(a, b, c, d, x[k + 13], S31, 0x289B7EC6);
        d = md5_HH(d, a, b, c, x[k + 0], S32, 0xEAA127FA);
        c = md5_HH(c, d, a, b, x[k + 3], S33, 0xD4EF3085);
        b = md5_HH(b, c, d, a, x[k + 6], S34, 0x4881D05);
        a = md5_HH(a, b, c, d, x[k + 9], S31, 0xD9D4D039);
        d = md5_HH(d, a, b, c, x[k + 12], S32, 0xE6DB99E5);
        c = md5_HH(c, d, a, b, x[k + 15], S33, 0x1FA27CF8);
        b = md5_HH(b, c, d, a, x[k + 2], S34, 0xC4AC5665);
        a = md5_II(a, b, c, d, x[k + 0], S41, 0xF4292244);
        d = md5_II(d, a, b, c, x[k + 7], S42, 0x432AFF97);
        c = md5_II(c, d, a, b, x[k + 14], S43, 0xAB9423A7);
        b = md5_II(b, c, d, a, x[k + 5], S44, 0xFC93A039);
        a = md5_II(a, b, c, d, x[k + 12], S41, 0x655B59C3);
        d = md5_II(d, a, b, c, x[k + 3], S42, 0x8F0CCC92);
        c = md5_II(c, d, a, b, x[k + 10], S43, 0xFFEFF47D);
        b = md5_II(b, c, d, a, x[k + 1], S44, 0x85845DD1);
        a = md5_II(a, b, c, d, x[k + 8], S41, 0x6FA87E4F);
        d = md5_II(d, a, b, c, x[k + 15], S42, 0xFE2CE6E0);
        c = md5_II(c, d, a, b, x[k + 6], S43, 0xA3014314);
        b = md5_II(b, c, d, a, x[k + 13], S44, 0x4E0811A1);
        a = md5_II(a, b, c, d, x[k + 4], S41, 0xF7537E82);
        d = md5_II(d, a, b, c, x[k + 11], S42, 0xBD3AF235);
        c = md5_II(c, d, a, b, x[k + 2], S43, 0x2AD7D2BB);
        b = md5_II(b, c, d, a, x[k + 9], S44, 0xEB86D391);
        a = md5_AddUnsigned(a, AA);
        b = md5_AddUnsigned(b, BB);
        c = md5_AddUnsigned(c, CC);
        d = md5_AddUnsigned(d, DD);
    }
    return (md5_WordToHex(a) + md5_WordToHex(b) + md5_WordToHex(c) + md5_WordToHex(d)).toLowerCase();
}

function encrypt1(txt, key) {
    let chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let nh = Math.floor(Math.random() * 64);
    let ch = chars.charAt(nh);
    let mdKey = md5(key + ch);
    mdKey = mdKey.substring(nh % 8, nh % 8 + (nh % 8 > 7 ? nh % 8 : nh % 8 + 17));
    txt = base64encode(txt);
    let tmp = '';
    let k = 0;
    for (let i = 0; i < txt.length; i++) {
        k = k == mdKey.length ? 0 : k;
        let charCode = txt.charCodeAt(i) ^ mdKey.charCodeAt(k++);
        tmp += String.fromCharCode(charCode);
    }
    return encodeURIComponent(ch + base64encode(tmp));
}

// Custom request wrapper to handle Bot validation
async function fetchWithBypass(url, postData) {
    let headers = JSON.parse(JSON.stringify(siteHeaders));
    if (globalCookie) headers["Cookie"] = globalCookie;

    let options = { headers: headers };
    if (postData) {
        options.method = "post";
        options.data = postData;
        headers["Content-Type"] = "application/x-www-form-urlencoded";
    }

    // Use TVBox native req()
    let r = await req(url, options);

    // Save cookies if any
    let sCookie = "";
    if (r.headers) {
        let sc = r.headers["set-cookie"] || r.headers["Set-Cookie"];
        if (sc) {
            if (Array.isArray(sc)) {
                sCookie = sc.map(c => c.split(';')[0]).join('; ');
            } else {
                sCookie = sc.split(';')[0];
            }
        }
    }
    if (sCookie) {
        globalCookie = sCookie;
        headers["Cookie"] = globalCookie;
    }

    let html = r.content || "";

    // Check if bot protection triggered
    if (html.includes("robot.php") || html.includes("var staticchars")) {
        console.log("Anti-bot triggered! Attempting bypass...");
        let staticMatch = html.match(/var\s+staticchars\s*=\s*['"]([^'"]+)['"]/);
        let tokenMatch1 = html.match(/var\s+token\s*=\s*['"]([^'"]+)['"]/);
        let tokenMatch2 = html.match(/var\s+token\s*=\s*encrypt\(['"]([^'"]+)['"]\)/);

        let verifyUrl = "";
        let verifyPost = "";

        if (staticMatch && tokenMatch1 && html.includes("math.random")) {
            // Challenge 1
            let stC = staticMatch[1];
            let tk = tokenMatch1[1];
            let p = encrypt1(stC, tk);
            verifyUrl = siteUrl + "/static/js/robot.php?p=" + p + "&" + tk + "=";
        } else if (staticMatch && tokenMatch2) {
            // Challenge 2 (Current PiPiShi active challenge)
            let tokenRaw = tokenMatch2[1];
            let staticchars = staticMatch[1];

            let encrypt2 = function (_str) {
                let encodechars = "";
                for (let i = 0; i < _str.length; i++) {
                    let num0 = staticchars.indexOf(_str[i]);
                    let code = num0 === -1 ? _str[i] : staticchars[(num0 + 3) % 62];
                    let num1 = Math.floor(Math.random() * 62);
                    let num2 = Math.floor(Math.random() * 62);
                    encodechars += staticchars.charAt(num1) + code + staticchars.charAt(num2);
                }
                return base64encode(encodechars);
            };

            let valueStr = encrypt2(url);
            let tokenStr = encrypt2(tokenRaw);
            verifyUrl = siteUrl + "/robot.php";
            verifyPost = "value=" + encodeURIComponent(valueStr) + "&token=" + encodeURIComponent(tokenStr);
        }

        if (verifyUrl) {
            let vOptions = { headers: headers };
            if (verifyPost) {
                vOptions.method = "post";
                vOptions.data = verifyPost;
                headers["Content-Type"] = "application/x-www-form-urlencoded";
            }
            // Send verification request
            let vRes = await req(verifyUrl, vOptions);

            // Re-fetch original URL with new cookies
            let sc2 = "";
            if (vRes.headers) {
                let hs2 = vRes.headers["set-cookie"] || vRes.headers["Set-Cookie"];
                if (hs2) {
                    sc2 = Array.isArray(hs2) ? hs2.map(c => c.split(';')[0]).join('; ') : hs2.split(';')[0];
                }
            }
            if (sc2) {
                globalCookie = sc2;
                headers["Cookie"] = globalCookie;
            }

            let finalRes = await req(url, { headers: headers });
            html = finalRes.content || "";
        }
    }
    return html;
}


// -------------------------------------------------------------
// TVBox Spider Required Methods
// -------------------------------------------------------------

async function init(cfg) {
    console.log("PiPiShi Native JS init");
}

async function home(filter) {
    console.log("PiPiShi home");
    let classes = [
        { type_id: "1", type_name: "电影" },
        { type_id: "2", type_name: "连续剧" },
        { type_id: "3", type_name: "综艺" },
        { type_id: "4", type_name: "动漫" }
    ];
    return JSON.stringify({
        class: classes,
        filters: {}
    });
}

async function homeVod() {
    console.log("PiPiShi homeVod");
    try {
        let html = await fetchWithBypass(siteUrl + "/");
        let list = parseVodList(html);
        return JSON.stringify({ list: list });
    } catch (e) {
        console.log("PiPiShi homeVod error: " + e);
        return JSON.stringify({ list: [] });
    }
}

async function category(tid, pg, filter, extend) {
    console.log("PiPiShi category: " + tid + ", pg: " + pg);
    try {
        let nPg = pg || 1;
        // The real endpoint for UI categories is /list/{id}--------{page}---.html
        let url = siteUrl + "/list/" + tid + "--------" + nPg + "---.html";
        let html = await fetchWithBypass(url);
        let list = parseVodList(html);

        return JSON.stringify({
            page: parseInt(nPg),
            pagecount: 99,
            limit: 20,
            total: 999,
            list: list
        });
    } catch (e) {
        console.log("PiPiShi category error: " + e);
        return JSON.stringify({ page: 1, pagecount: 1, list: [] });
    }
}

async function detail(id) {
    console.log("PiPiShi detail: " + id);
    try {
        let url = siteUrl + "/vod/" + id + ".html";
        let html = await fetchWithBypass(url);

        let vod = {
            vod_id: id,
            vod_name: "",
            vod_pic: "",
            vod_remarks: "",
            vod_play_from: "PiPiShi",
            vod_play_url: ""
        };

        let titleMatch = html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/);
        if (titleMatch) {
            vod.vod_name = titleMatch[1].replace(/<[^>]+>/g, "").trim();
        }

        let playLinks = [];
        let playLinkRegex = /href=["'](\/play\/[0-9]+-[0-9]+-[0-9]+\.html)["'][^>]*>([\s\S]*?)<\/a>/g;
        let pMatch;
        while ((pMatch = playLinkRegex.exec(html)) !== null) {
            let linkUrl = pMatch[1];
            let linkName = pMatch[2].replace(/<[^>]+>/g, "").trim();
            playLinks.push(linkName + "$" + linkUrl);
        }

        if (playLinks.length > 0) {
            vod.vod_play_url = playLinks.join("#");
        }

        return JSON.stringify({ list: [vod] });
    } catch (e) {
        console.log("PiPiShi detail error: " + e);
        return JSON.stringify({ list: [] });
    }
}

async function search(wd, quick) {
    console.log("PiPiShi search: " + wd);
    try {
        let url = siteUrl + "/search/-------------.html?wd=" + encodeURIComponent(wd);
        let html = await fetchWithBypass(url);

        let list = parseVodList(html);
        return JSON.stringify({ page: 1, pagecount: 1, list: list });
    } catch (e) {
        console.log("PiPiShi search error: " + e);
        return JSON.stringify({ page: 1, pagecount: 1, list: [] });
    }
}

async function play(flag, id, flags) {
    console.log("PiPiShi play: " + id);
    try {
        let url = siteUrl + id;
        let html = await fetchWithBypass(url);

        let playerMatch = html.match(/player_aaaa=({.*?})<\/script>/);
        if (!playerMatch) {
            return JSON.stringify({ parse: 0, url: "" });
        }

        let playerData = JSON.parse(playerMatch[1]);
        let encUrl = playerData.url;

        let apiUrl = siteUrl + "/lionplay/api.php";
        let formBody = "vid=" + encodeURIComponent(encUrl) + "&url=" + encodeURIComponent(encUrl);

        let apiHeaders = JSON.parse(JSON.stringify(siteHeaders));
        if (globalCookie) apiHeaders["Cookie"] = globalCookie;
        apiHeaders["Content-Type"] = "application/x-www-form-urlencoded";

        let apiReq = await req(apiUrl, {
            method: "post",
            data: formBody,
            headers: apiHeaders
        });

        let apiRes = JSON.parse(apiReq.content);

        if (apiRes && apiRes.code === 200 && apiRes.data && apiRes.data.url) {
            let finalUrl = PIPISHI_DECODE(apiRes.data.url);
            console.log("PiPiShi Final Decoded: " + finalUrl);
            return JSON.stringify({
                parse: 0,
                url: finalUrl,
                header: siteHeaders
            });
        }
    } catch (e) {
        console.log("PiPiShi play error: " + e.message);
    }
    return JSON.stringify({ parse: 0, url: "" });
}

// -------------------------------------------------------------
// Helper Methods
// -------------------------------------------------------------

function parseVodList(html) {
    let list = [];
    let block = html;
    let blockMatch = html.match(/<div class="module-main module-page[^>]*>([\s\S]*?)<div id="page">/);
    if (blockMatch) {
        block = blockMatch[1];
    } else {
        let blockMatch2 = html.match(/class="module-items[^>]*>([\s\S]*?)<\/div>\s*<\/div>/);
        if (blockMatch2) block = blockMatch2[1];
    }

    let splitArr = block.split('<a');
    for (let i = 1; i < splitArr.length; i++) {
        let chunk = splitArr[i];
        if (chunk.indexOf('href="/vod/') === -1) continue;

        let aEnd = chunk.indexOf('</a>');
        if (aEnd !== -1) chunk = chunk.substring(0, aEnd);

        let idMatch = chunk.match(/href="\/vod\/([0-9]+)\.html"/);
        let titleMatch = chunk.match(/title="([^"]+)"/);
        let picMatch = chunk.match(/data-original="([^"]+)"/);
        if (!picMatch) picMatch = chunk.match(/data-src="([^"]+)"/);
        let remarkMatch = chunk.match(/class="module-item-note"[^>]*>([^<]*)/);
        if (!remarkMatch) remarkMatch = chunk.match(/class="pic-text[^>]*>([^<]*)/);

        if (idMatch && titleMatch && picMatch) {
            list.push({
                vod_id: idMatch[1],
                vod_name: titleMatch[1],
                vod_pic: picMatch[1],
                vod_remarks: remarkMatch ? remarkMatch[1].trim() : ""
            });
        }
    }
    return list;
}

// 导出插件接口
export default {
    $cfg,
    init,
    home,
    homeVod,
    category,
    detail,
    search,
    play
};
