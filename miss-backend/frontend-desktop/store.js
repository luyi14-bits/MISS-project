(function(){
  var STORAGE_KEY = 'miss_roles';

  window.getRoles = function(){
    try {
      var raw = sessionStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch(e) { return []; }
  };

  window.saveRole = function(name, profile, background){
    var roles = getRoles();
    var existing = roles.findIndex(function(r){ return r.name === name; });
    var entry = { name: name, profile: profile, background: background || '' };
    if(existing >= 0){
      roles[existing] = entry;
    } else {
      roles.push(entry);
    }
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(roles)); } catch(e){}
    return true;
  };

  window.deleteRole = function(name){
    var roles = getRoles();
    roles = roles.filter(function(r){ return r.name !== name; });
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(roles)); } catch(e){}
    return true;
  };

  window.importRole = function(jsonData){
    if(!jsonData.name || !jsonData.profile) return false;
    return saveRole(jsonData.name, jsonData.profile, jsonData.background || '');
  };

  window.getBuiltinRoles = function(){
    return [
      { name: '傲娇女友', profile: {independent_submissive:-100,intimacy:100,aggression:40,rational_emotional:60}, background: '' },
      { name: '知性姐姐', profile: {education_level:90,curiosity:80,humor:40,aggression:-50,social_energy:30}, background: '' },
      { name: '笨蛋⑨', profile: {education_level:-100,curiosity:100,humor:60,social_energy:30}, background: '' },
      { name: '冰山美人', profile: {rational_emotional:-100,aggression:-100,independent_submissive:-100,social_energy:-100}, background: '' }
    ];
  };

  window.getBuiltinAvatars = function(){
    return {
      '傲娇女友': 'assets/avatar-preset-tsundere.jpg',
      '知性姐姐': 'assets/avatar-preset-intellectual.jpg',
      '笨蛋⑨': 'assets/avatar-preset-baka.jpg',
      '冰山美人': 'assets/avatar-preset-icequeen.jpg'
    };
  };
})();
