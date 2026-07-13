/* ── MISS Desktop App Script ── */
(function(){
  var API_BASE = 'http://127.0.0.1:8000';

  var profile = {};
  var appliedProfile = {};
  var appliedBackground = '';
  var ATTRS = ['rational_emotional','willpower','independent_submissive','education_level','intimacy','curiosity','humor','aggression','social_energy','adventurousness'];
  ATTRS.forEach(function(a){ profile[a]=0;appliedProfile[a]=0; });

  var activePreset = null;
  var activePresetName = 'miss-default';
  var ctxTarget = null;
  var toastTimer = null;
  var sessionId = sessionStorage.getItem('miss_session_id') || crypto.randomUUID();
  sessionStorage.setItem('miss_session_id', sessionId);

  /* ── 启动加载流程 ── */
  var LOADING_INTERVAL = null;
  (function healthPoll(){
    LOADING_INTERVAL = setInterval(function(){
      fetch(API_BASE + '/health').then(function(r){
        if(r.ok){
          clearInterval(LOADING_INTERVAL);
          document.getElementById('loadingStatus').textContent = '就绪，正在加载...';
          setTimeout(function(){
            var ls = document.getElementById('loadingScreen');
            if(ls) ls.style.display = 'none';
            renderSidebarRoles();
            if(typeof lucide !== 'undefined' && lucide.createIcons) lucide.createIcons();
          }, 300);
        }
      }).catch(function(){});
    }, 800);
  })();

  /* ── 角色数据 ── */
  var PRESETS_CACHE = {};
  function loadAllRoles(){
    var builtins = getBuiltinRoles();
    var saved = getRoles();
    PRESETS_CACHE = {};
    builtins.forEach(function(r){ PRESETS_CACHE[r.name] = r; });
    saved.forEach(function(r){ PRESETS_CACHE[r.name] = r; });
  }

  var PRESET_AVATARS = getBuiltinAvatars();

  function renderSidebarRoles(){
    loadAllRoles();
    var container = document.querySelector('#sidebarExpanded .px-2\\.5:nth-child(3)');
    if(!container) return;
    var cards = container.querySelectorAll('.preset-card');
    cards.forEach(function(c){ c.remove(); });
    Object.keys(PRESETS_CACHE).forEach(function(name){
      var r = PRESETS_CACHE[name];
      var div = document.createElement('div');
      div.className = 'preset-card role-card';
      div.dataset.preset = name;
      var img = document.createElement('img');
      img.src = PRESET_AVATARS[name] || 'assets/avatar-miss-default.jpg';
      img.alt = name;
      img.className = 'w-6 h-6 rounded-full object-cover shrink-0';
      img.style.cssText = 'border:1.5px solid var(--color-primary-light);box-shadow:0 1px 3px rgba(74,55,40,0.08);';
      div.appendChild(img);
      var span = document.createElement('span');
      span.className = 'truncate';
      span.textContent = name;
      div.appendChild(span);
      var tooltip = document.createElement('div');
      tooltip.className = 'preset-tooltip';
      var prof = r.profile;
      var pills = [];
      Object.keys(prof).forEach(function(k){
        if(prof[k] !== 0 && prof[k] !== undefined){
          pills.push('<span class="tooltip-pill">'+k+' '+prof[k]+'</span>');
        }
      });
      tooltip.innerHTML = pills.slice(0,4).join('');
      div.appendChild(tooltip);
      container.insertBefore(div, container.firstChild);
    });
  }

  function applyRoleByName(name){
    loadAllRoles();
    var r = PRESETS_CACHE[name];
    if(!r) return;
    setProfileVals(r.profile);
    applyProfile();
    activePresetName = name;
    appliedBackground = r.background || '';
    toastMsg('已应用角色：'+name);
  }

  /* ── 侧边栏 ── */
  function toggleSidebar(){
    document.getElementById('sidebar').classList.toggle('collapsed');
  }

  function switchSession(el, name){
    document.querySelectorAll('.sidebar-item[data-sid]').forEach(function(i){ i.classList.remove('active'); });
    el.classList.add('active');
    document.getElementById('sessionTitle').textContent = name;
  }

  function addSession(){
    sessionId = crypto.randomUUID();
    sessionStorage.setItem('miss_session_id', sessionId);
    document.getElementById('chatMsgs').innerHTML = '';
    var es = document.getElementById('emptyState');
    if(!es) {
      es = document.createElement('div'); es.id = 'emptyState'; es.className = 'flex flex-col items-center justify-center h-full';
      es.style.cssText = 'gap:16px;';
      es.innerHTML = '<div class="flex flex-col items-center" style="gap:24px;"><div class="relative" style="width:100px;height:100px;"><div class="absolute inset-0 rounded-full" style="background:radial-gradient(circle, var(--color-primary-light) 0%, transparent 70%);opacity:0.5;"></div><div class="absolute rounded-full" style="top:8px;left:50%;margin-left:-2px;width:4px;height:4px;background:var(--color-primary);opacity:0.6;animation:sparkleFloat 2s ease-in-out infinite;"></div><div class="absolute rounded-full" style="top:20px;right:20px;width:3px;height:3px;background:var(--state-warning);opacity:0.5;animation:sparkleFloat 2.5s ease-in-out 0.5s infinite;"></div><div class="absolute rounded-full" style="bottom:25px;left:18px;width:3px;height:3px;background:var(--color-primary);opacity:0.4;animation:sparkleFloat 3s ease-in-out 1s infinite;"></div><img src="assets/avatar-miss-default.jpg" alt="MISS" class="w-full h-full rounded-full object-cover" style="border:2px solid var(--color-primary-light);box-shadow:0 2px 8px rgba(74,55,40,0.08);"></div><div class="flex flex-col items-center" style="gap:8px;"><span class="text-center" style="font-size:var(--font-size-lg);font-weight:600;color:var(--color-text);">新对话已创建 ✦</span><span style="font-size:var(--font-size-sm);color:var(--color-text-secondary);">选择一个角色，或直接发送消息</span></div></div>';
      document.getElementById('chatMsgs').appendChild(es);
    } else {
      es.style.display = 'flex';
    }
    toastMsg('已创建新对话');
  }

  /* ── 属性控制 ── */
  function getSliderEl(attr){
    return document.querySelector('input[type="range"][data-attr="'+attr+'"]');
  }
  function getNumEl(attr){
    return document.querySelector('input[type="number"][data-attr="'+attr+'"]');
  }

  function syncControls(attr, val){
    var sl = getSliderEl(attr); if(sl) sl.value = val;
    var ni = getNumEl(attr); if(ni) ni.value = val;
    var dirty = document.getElementById('d_'+attr);
    if(dirty) dirty.classList.toggle('visible', val !== appliedProfile[attr]);
    if(attr === 'education_level'){ toggleCirnoTheme(val); }
  }

  function toggleCirnoTheme(val){
    if(val === -100){
      document.documentElement.setAttribute('data-theme','cirno');
      var badge = document.getElementById('cirnoBadge');
      if(badge) badge.classList.add('show');
    } else {
      document.documentElement.removeAttribute('data-theme');
      var badge = document.getElementById('cirnoBadge');
      if(badge) badge.classList.remove('show');
    }
  }

  function onSlider(slider){
    var attr = slider.dataset.attr; profile[attr] = parseInt(slider.value); syncControls(attr, profile[attr]);
  }

  function onNumInput(input){
    var attr = input.dataset.attr; var val = parseInt(input.value); var min = attr === 'intimacy' ? 0 : -100;
    if(isNaN(val)) val = min < 0 ? 0 : min; if(val < min) val = min; if(val > 100) val = 100;
    input.value = val; profile[attr] = val; syncControls(attr, val);
  }

  function applyProfile(){
    ATTRS.forEach(function(a){ appliedProfile[a]=profile[a]; });
    document.querySelectorAll('.attr-dirty-dot').forEach(function(d){ d.classList.remove('visible'); });
    toastMsg('属性已应用');
  }

  function resetAll(){
    ATTRS.forEach(function(a){ profile[a]=0;appliedProfile[a]=0;syncControls(a,0); });
    document.documentElement.removeAttribute('data-theme');
    var badge = document.getElementById('cirnoBadge'); if(badge) badge.classList.remove('show');
    appliedBackground = '';
    activePresetName = 'miss-default';
    toastMsg('属性已重置');
  }

  /* ── 内心独白 ── */
  function toggleInner(bubble){
    var inner = bubble.parentElement.querySelector('.msg-inner');
    if(inner) inner.classList.toggle('expanded');
  }

  function toggleAllInner(){
    var show = document.getElementById('showInner').checked;
    document.querySelectorAll('.msg-inner').forEach(function(el){ el.classList.toggle('expanded',show); });
  }

  /* ── 表情 ── */
  function toggleEmojiPanel(){
    document.getElementById('emojiPanel').classList.toggle('show');
  }

  function insertEmoji(emoji){
    var input = document.getElementById('msgInput'); input.value += emoji; input.focus(); document.getElementById('emojiPanel').classList.remove('show');
  }

  /* ── 右键菜单 ── */
  var CTX_ROLE_NAME = null;
  function showContextMenu(e, el){
    e.preventDefault(); ctxTarget = el;
    CTX_ROLE_NAME = el.dataset.preset;
    var menu = document.getElementById('ctxMenu');
    menu.style.left = e.clientX+'px'; menu.style.top = e.clientY+'px'; menu.classList.add('show');
  }

  function applyPresetFromMenu(){
    if(!CTX_ROLE_NAME) return;
    applyRoleByName(CTX_ROLE_NAME);
  }

  function exportRoleFromMenu(){
    if(!CTX_ROLE_NAME) return;
    loadAllRoles();
    var r = PRESETS_CACHE[CTX_ROLE_NAME];
    if(!r) return;
    var exportData = { version: '1.1', name: r.name, profile: r.profile, background: r.background || '' };
    var blob = new Blob([JSON.stringify(exportData, null, 2)], {type: 'application/json'});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'miss_role_' + r.name + '.json';
    a.click();
    URL.revokeObjectURL(url);
    toastMsg('已导出');
  }

  function deleteRoleFromMenu(){
    if(!CTX_ROLE_NAME) return;
    deleteRole(CTX_ROLE_NAME);
    renderSidebarRoles();
    toastMsg('角色已删除');
  }

  function closeContextMenu(){
    document.getElementById('ctxMenu').classList.remove('show');
    ctxTarget = null;
    CTX_ROLE_NAME = null;
  }

  function setProfileVals(vals){
    ATTRS.forEach(function(a){ if(vals[a] !== undefined){ profile[a]=vals[a];syncControls(a,vals[a]); } });
  }

  /* ── 角色 CRUD (本地存储) ── */
  function createPreset(){
    openNewPresetModal();
  }

  function saveCurrentPreset(){
    var defaultName = activePresetName !== 'miss-default' ? activePresetName : '新角色';
    var name = prompt('角色名称：', defaultName); if(!name) return;
    saveRole(name, appliedProfile, appliedBackground);
    activePresetName = name;
    renderSidebarRoles();
    toastMsg('已保存：'+name);
  }

  function importPresetFile(){
    var inp = document.createElement('input'); inp.type='file'; inp.accept='.json';
    inp.onchange = function(){
      if(!inp.files[0]) return;
      var reader = new FileReader();
      reader.onload = function(e){
        try {
          var data = JSON.parse(e.target.result);
          var name = data.name || data.preset_name || '导入角色';
          var prof = data.profile || data;
          if(!name || !prof) { toastMsg('JSON 格式无效'); return; }
          if(importRole({name: name, profile: prof, background: data.background || ''})){
            renderSidebarRoles();
            toastMsg('已导入：'+name);
          } else {
            toastMsg('导入失败');
          }
        } catch(ex) { toastMsg('JSON 解析失败'); }
      };
      reader.readAsText(inp.files[0]);
    };
    inp.click();
  }

  /* ── 消息构建 ── */
  function escapeHtml(s){ var d=document.createElement('div');d.textContent=s;return d.innerHTML; }

  function buildMsgHTML(type, avatarHtml, sender, text, innerText){
    var h='<div class="msg-row '+type+' msg-animate">'+avatarHtml+'<div class="msg-body"><div class="msg-sender">'+escapeHtml(sender)+'</div>';
    if(text){ h+='<div class="msg-bubble">'+escapeHtml(text)+'</div>'; }
    if(innerText){
        var expanded = document.getElementById('showInner').checked ? ' expanded' : '';
        h+='<div class="msg-inner'+expanded+'">'+escapeHtml(innerText)+'</div>';
    }
    h+='</div></div>'; return h;
  }

  function buildUserAvatarHTML(){
    return '<div class="msg-avatar user-avatar"><span class="avatar-user-icon">✦</span></div>';
  }

  function getMissName(){
    return activePresetName !== 'miss-default' ? activePresetName : 'MISS';
  }

  function buildMissAvatarHTML(){
    loadAllRoles();
    var src = PRESET_AVATARS[activePresetName] || 'assets/avatar-miss-default.jpg';
    return '<div class="msg-avatar miss-avatar"><img src="'+src+'" alt="MISS"></div>';
  }

  /* ── API: 发送消息 ── */
  function sendMsg(){
    var input = document.getElementById('msgInput'); var msg = input.value.trim(); if(!msg) return;
    var container = document.getElementById('chatMsgs'); input.value = '';
    var emptyState = document.getElementById('emptyState'); if(emptyState) emptyState.style.display = 'none';
    container.insertAdjacentHTML('beforeend', buildMsgHTML('user', buildUserAvatarHTML(), '我', msg));

    var typingHTML = '<div class="msg-row miss msg-animate" id="typingIndicator">'+buildMissAvatarHTML()+'<div class="msg-body"><div class="msg-sender">'+escapeHtml(getMissName())+'</div><div class="msg-bubble typing-indicator"><span></span><span></span><span></span></div></div></div>';
    container.insertAdjacentHTML('beforeend', typingHTML);
    container.scrollTop = container.scrollHeight;

    setSending(true);
    fetch(API_BASE + '/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId,message:msg,profile:appliedProfile,background:appliedBackground})})
      .then(function(r){ return r.json(); })
      .then(function(data){
        var typingEl = document.getElementById('typingIndicator'); if(typingEl) typingEl.remove();
        container.insertAdjacentHTML('beforeend', buildMsgHTML('miss', buildMissAvatarHTML(), getMissName(), data.spoken, data.inner_thought));
        container.scrollTop = container.scrollHeight; setSending(false);

        if(data.intimacy_change !== undefined && data.intimacy_change !== 0){
            var newVal = data.intimacy;
            profile['intimacy'] = newVal;
            appliedProfile['intimacy'] = newVal;
            syncControls('intimacy', newVal);
            if(data.intimacy_change > 0){
                toastMsg('亲密度 +' + data.intimacy_change);
            } else if(data.intimacy_change < 0){
                toastMsg('亲密度 ' + data.intimacy_change);
            }
        }
      })
      .catch(function(e){
        var typingEl = document.getElementById('typingIndicator'); if(typingEl) typingEl.remove();
        container.insertAdjacentHTML('beforeend', buildMsgHTML('miss', buildMissAvatarHTML(), getMissName(), '嗯...我好像走神了。再说一遍好吗？', ''));
        container.scrollTop = container.scrollHeight; setSending(false);
      });
  }

  function setSending(active){
    document.getElementById('sendBtn').disabled = active;
    document.getElementById('msgInput').disabled = active;
  }

  /* ── 图片上传模拟 ── */
  function simulateImageUpload(){
    var container = document.getElementById('chatMsgs'); var emptyState = document.getElementById('emptyState'); if(emptyState) emptyState.style.display='none';
    container.insertAdjacentHTML('beforeend','<div class="msg-row user msg-animate">'+buildUserAvatarHTML()+'<div class="msg-body"><div class="msg-sender">我</div><div class="img-placeholder">🖼</div><div class="msg-bubble">[图片] 📷</div></div></div>');
    container.scrollTop = container.scrollHeight;
    setTimeout(function(){ sendToBackend('[图片]'); },200);
  }

  function sendToBackend(msg){
    fetch(API_BASE + '/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId,message:msg,profile:appliedProfile,background:appliedBackground})})
      .then(function(r){return r.json();}).then(function(data){ document.getElementById('chatMsgs').insertAdjacentHTML('beforeend',buildMsgHTML('miss',buildMissAvatarHTML(),getMissName(),data.spoken,data.inner_thought)); document.getElementById('chatMsgs').scrollTop=document.getElementById('chatMsgs').scrollHeight; }).catch(function(){});
  }

  function previewPlaceholder(){ toastMsg('图片预览（演示模式）'); }

  function closePreview(){ document.getElementById('imgOverlay').classList.add('hidden'); }

  /* ── Toast ── */
  function toastMsg(msg){
    var el = document.getElementById('toast'); el.textContent = msg; el.classList.add('show');
    clearTimeout(toastTimer); toastTimer = setTimeout(function(){ el.classList.remove('show'); }, 1800);
  }

  /* ── API 设置 (sessionStorage) ── */
  function onModelSelect(val){
    var custom = document.getElementById('settingsModelCustom');
    if(val === '__custom__'){
      custom.classList.remove('hidden');
      custom.focus();
    } else {
      custom.classList.add('hidden');
      if(val.startsWith('deepseek')){
        document.getElementById('settingsBaseUrl').value = 'https://api.deepseek.com/v1';
      } else {
        if(!document.getElementById('settingsBaseUrl').value || document.getElementById('settingsBaseUrl').value.indexOf('deepseek') !== -1){
          document.getElementById('settingsBaseUrl').value = '';
        }
      }
    }
  }

  function openSettings(){
    document.getElementById('settingsModal').classList.remove('hidden');
    var select = document.getElementById('settingsModel');
    var saved = sessionStorage.getItem('miss_settings');
    var d = saved ? JSON.parse(saved) : {};
    if(d.openai_api_key){ document.getElementById('settingsApiKey').value = d.openai_api_key || ''; }
    if(d.openai_base_url){ document.getElementById('settingsBaseUrl').value = d.openai_base_url; }
    var model = d.model || 'gpt-4o';
    var matched = false;
    for(var i=0;i<select.options.length;i++){
      if(select.options[i].value === model && select.options[i].value !== '__custom__'){
        select.value = model; matched = true; break;
      }
    }
    if(!matched && model){
      select.value = '__custom__';
      var custom = document.getElementById('settingsModelCustom');
      custom.classList.remove('hidden');
      custom.value = model;
    } else {
      document.getElementById('settingsModelCustom').classList.add('hidden');
    }
    onModelSelect(select.value);
  }

  function closeSettings(){
    document.getElementById('settingsModal').classList.add('hidden');
  }

  function toggleApiKeyVisibility(){
    var inp = document.getElementById('settingsApiKey');
    inp.type = document.getElementById('showApiKey').checked ? 'text' : 'password';
  }

  function saveSettings(){
    var apiKey = document.getElementById('settingsApiKey').value.trim();
    var baseUrl = document.getElementById('settingsBaseUrl').value.trim();
    var modelSelect = document.getElementById('settingsModel');
    var model = modelSelect.value === '__custom__' ? document.getElementById('settingsModelCustom').value.trim() : modelSelect.value;
    if(!model) model = 'gpt-4o';
    var settings = { openai_api_key: apiKey, openai_base_url: baseUrl, model: model };
    sessionStorage.setItem('miss_settings', JSON.stringify(settings));
    postSettingsToBackend(settings);
    toastMsg('设置已保存 ✓');
    closeSettings();
  }

  function postSettingsToBackend(settings){
    fetch(API_BASE + '/api/settings', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        openai_api_key: settings.openai_api_key || null,
        openai_base_url: settings.openai_base_url || null,
        model: settings.model || null
      })
    }).catch(function(){});
  }

  /* ── 新建角色弹窗 ── */
  function openNewPresetModal(){
    document.getElementById('newPresetModal').classList.remove('hidden');
    document.getElementById('newPresetName').focus();
    document.getElementById('newPresetStatus').textContent = '';
  }

  function closeNewPresetModal(){
    document.getElementById('newPresetModal').classList.add('hidden');
  }

  async function createPresetFromModal(){
    var name = document.getElementById('newPresetName').value.trim();
    var desc = document.getElementById('newPresetDesc').value.trim();
    var bg = document.getElementById('newPresetBackground').value.trim();
    var statusEl = document.getElementById('newPresetStatus');
    var btn = document.getElementById('newPresetBtn');

    if(!name){ toastMsg('请输入角色名称'); return; }
    if(!desc){ toastMsg('请输入角色描述'); return; }

    btn.disabled = true;
    btn.textContent = '⏳ 分析中...';
    statusEl.textContent = '正在分析角色属性...';

    try {
      var resp = await fetch(API_BASE + '/api/character/analyze', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({description: desc})
      });
      if(!resp.ok){
        var errData = await resp.json().catch(function(){ return {}; });
        throw new Error(errData.detail || '分析失败');
      }
      var data = await resp.json();
      ATTRS.forEach(function(a){
        if(data.profile[a] !== undefined){
          profile[a] = data.profile[a];
          syncControls(a, data.profile[a]);
        }
      });
      applyProfile();
      statusEl.textContent = '属性分析完成，正在保存...';
    } catch(e) {
      statusEl.textContent = '';
      btn.disabled = false;
      btn.textContent = '✨ 生成并创建';
      toastMsg('生成失败：' + e.message);
      return;
    }

    saveRole(name, appliedProfile, bg);
    activePresetName = name;
    appliedBackground = bg;
    renderSidebarRoles();
    toastMsg('已创建：' + name);
    closeNewPresetModal();

    btn.disabled = false;
    btn.textContent = '✨ 生成并创建';
    statusEl.textContent = '';
    document.getElementById('newPresetName').value = '';
    document.getElementById('newPresetDesc').value = '';
    document.getElementById('newPresetBackground').value = '';
  }

  /* ── 初始化 ── */
  function init(){
    var sidebar = document.getElementById('sidebar');
    sidebar.classList.remove('collapsed');

    var sidebarToggle = document.getElementById('sidebarToggle');
    if(sidebarToggle) sidebarToggle.addEventListener('click', toggleSidebar);

    var btnNewSession = document.getElementById('btnNewSession');
    if(btnNewSession) btnNewSession.addEventListener('click', addSession);

    var sidebarExpanded = document.getElementById('sidebarExpanded');
    if(sidebarExpanded) {
      sidebarExpanded.addEventListener('click', function(e){
        var roleCard = e.target.closest('.role-card');
        if(roleCard){
          var name = roleCard.dataset.preset;
          if(name) applyRoleByName(name);
          return;
        }
        var sessionItem = e.target.closest('.sidebar-item[data-sid]');
        if(sessionItem){
          var sessionName = sessionItem.querySelector('span:last-child');
          var displayName = sessionName ? sessionName.textContent.trim() : '';
          switchSession(sessionItem, displayName);
        }
      });

      sidebarExpanded.addEventListener('contextmenu', function(e){
        var roleCard = e.target.closest('.role-card');
        if(roleCard) showContextMenu(e, roleCard);
      });
    }

    var btnNewPreset = document.getElementById('btnNewPreset');
    if(btnNewPreset) btnNewPreset.addEventListener('click', createPreset);

    var btnSavePreset = document.getElementById('btnSavePreset');
    if(btnSavePreset) btnSavePreset.addEventListener('click', saveCurrentPreset);

    var btnImportPreset = document.getElementById('btnImportPreset');
    if(btnImportPreset) btnImportPreset.addEventListener('click', importPresetFile);

    var ctxMenuApply = document.getElementById('ctxMenuApply');
    if(ctxMenuApply) ctxMenuApply.addEventListener('click', applyPresetFromMenu);

    var ctxMenuExport = document.getElementById('ctxMenuExport');
    if(ctxMenuExport) ctxMenuExport.addEventListener('click', exportRoleFromMenu);

    var ctxMenuDelete = document.getElementById('ctxMenuDelete');
    if(ctxMenuDelete) ctxMenuDelete.addEventListener('click', deleteRoleFromMenu);

    document.addEventListener('click', function(e){
      var menu = document.getElementById('ctxMenu');
      if(!menu.contains(e.target)) closeContextMenu();
    });

    var showInner = document.getElementById('showInner');
    if(showInner) showInner.addEventListener('change', toggleAllInner);

    var emojiPickerBtn = document.querySelector('.emoji-picker-btn');
    if(emojiPickerBtn) emojiPickerBtn.addEventListener('click', toggleEmojiPanel);

    var emojiPanel = document.getElementById('emojiPanel');
    if(emojiPanel){
      emojiPanel.addEventListener('click', function(e){
        var emojiItem = e.target.closest('.emoji-item');
        if(emojiItem){
          var emoji = emojiItem.getAttribute('data-emoji');
          if(emoji) insertEmoji(emoji);
        }
      });
    }

    document.addEventListener('click', function(e){
      var p = document.getElementById('emojiPanel');
      if(p && !p.contains(e.target) && !e.target.closest('.emoji-picker-btn')) p.classList.remove('show');
    });

    var btnImageUpload = document.getElementById('btnImageUpload');
    if(btnImageUpload) btnImageUpload.addEventListener('click', simulateImageUpload);

    var msgInput = document.getElementById('msgInput');
    if(msgInput){
      msgInput.addEventListener('keydown', function(e){
        if(e.key === 'Enter' && !e.shiftKey){
          e.preventDefault();
          sendMsg();
        }
      });
    }

    var sendBtn = document.getElementById('sendBtn');
    if(sendBtn) sendBtn.addEventListener('click', sendMsg);

    var chatMsgs = document.getElementById('chatMsgs');
    if(chatMsgs){
      chatMsgs.addEventListener('click', function(e){
        var bubble = e.target.closest('.msg-bubble');
        if(bubble && bubble.closest('.msg-row.miss') && !bubble.classList.contains('typing-indicator')){
          var inner = bubble.parentElement.querySelector('.msg-inner');
          if(inner) inner.classList.toggle('expanded');
          return;
        }
        var placeholder = e.target.closest('.img-placeholder');
        if(placeholder){
          previewPlaceholder();
        }
      });
    }

    var attrContainer = document.getElementById('attrContainer');
    if(attrContainer){
      attrContainer.addEventListener('input', function(e){
        var slider = e.target.closest('.attr-slider');
        if(slider) onSlider(slider);
      });

      attrContainer.addEventListener('change', function(e){
        var numInput = e.target.closest('.attr-num-input');
        if(numInput) onNumInput(numInput);
      });

      attrContainer.addEventListener('keydown', function(e){
        if(e.key === 'Enter'){
          var numInput = e.target.closest('.attr-num-input');
          if(numInput){
            e.preventDefault();
            onNumInput(numInput);
          }
        }
      });
    }

    var btnReset = document.getElementById('btnReset');
    if(btnReset) btnReset.addEventListener('click', resetAll);

    var btnApply = document.getElementById('btnApply');
    if(btnApply) btnApply.addEventListener('click', applyProfile);

    var imgOverlay = document.getElementById('imgOverlay');
    if(imgOverlay) imgOverlay.addEventListener('click', closePreview);

    var btnOpenSettings = document.getElementById('btnOpenSettings');
    if(btnOpenSettings) btnOpenSettings.addEventListener('click', openSettings);

    var btnCloseSettings = document.getElementById('btnCloseSettings');
    if(btnCloseSettings) btnCloseSettings.addEventListener('click', closeSettings);

    var btnCancelSettings = document.getElementById('btnCancelSettings');
    if(btnCancelSettings) btnCancelSettings.addEventListener('click', closeSettings);

    var btnSaveSettings = document.getElementById('btnSaveSettings');
    if(btnSaveSettings) btnSaveSettings.addEventListener('click', saveSettings);

    var settingsModal = document.getElementById('settingsModal');
    if(settingsModal){
      settingsModal.addEventListener('click', function(e){
        if(e.target === e.currentTarget) closeSettings();
      });
      var settingsInner = settingsModal.querySelector('div');
      if(settingsInner){
        settingsInner.addEventListener('click', function(e){ e.stopPropagation(); });
      }
    }

    var showApiKey = document.getElementById('showApiKey');
    if(showApiKey) showApiKey.addEventListener('change', toggleApiKeyVisibility);

    var settingsModel = document.getElementById('settingsModel');
    if(settingsModel){
      settingsModel.addEventListener('change', function(){
        onModelSelect(settingsModel.value);
      });
    }

    var btnCloseNewPreset = document.getElementById('btnCloseNewPreset');
    if(btnCloseNewPreset) btnCloseNewPreset.addEventListener('click', closeNewPresetModal);

    var btnCancelNewPreset = document.getElementById('btnCancelNewPreset');
    if(btnCancelNewPreset) btnCancelNewPreset.addEventListener('click', closeNewPresetModal);

    var newPresetBtn = document.getElementById('newPresetBtn');
    if(newPresetBtn) newPresetBtn.addEventListener('click', createPresetFromModal);

    var newPresetModal = document.getElementById('newPresetModal');
    if(newPresetModal){
      newPresetModal.addEventListener('click', function(e){
        if(e.target === e.currentTarget) closeNewPresetModal();
      });
      var newPresetInner = newPresetModal.querySelector('div');
      if(newPresetInner){
        newPresetInner.addEventListener('click', function(e){ e.stopPropagation(); });
      }
    }
  }

  init();
})();
