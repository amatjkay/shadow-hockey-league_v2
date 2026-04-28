/**
 * Shadow Hockey League - Admin Autofill Logic
 */

(function(window, $) {
    'use strict';

    window.SHLAdmin = {
        /**
         * Initialize Country Autofill
         * @param {Object} flagMap - Mapping of country codes to flag image paths
         */
        initCountryAutofill: function(flagMap) {
            var $code = $('#code');
            var $name = $('#name');
            var $flag = $('#flag_path');
            var $preview = $('#flag-preview-img');

            function updateCountryDetails() {
                setTimeout(function() {
                    var data = $code.select2('data');
                    if (data && data.length > 0) {
                        var val = data[0];
                        // Update Name if empty or unknown
                        if ($name.val() === '' || $name.val() === 'Unknown') {
                            $name.val(val.text);
                        }
                        // Update Flag if mapping exists
                        var flagUrl = flagMap[val.id];
                        if (flagUrl) {
                            $flag.val(flagUrl).trigger('change');
                            $preview.attr('src', flagUrl).show();
                        }
                    }
                }, 50);
            }

            $code.on('select2:select', updateCountryDetails);

            // Initial check on load
            if ($code.val()) {
                setTimeout(updateCountryDetails, 1000);
            }
        },

        /**
         * Initialize Achievement Autofill
         * @param {Array} types - Array of achievement types [id, name, code, bp_l1, bp_l2]
         * @param {Array} leagues - Array of leagues [id, name, code]
         * @param {Array} seasons - Array of seasons [id, name, code, mult]
         */
        initAchievementAutofill: function(types, leagues, seasons) {
            var $type = $('#type_id');
            var $league = $('#league_id');
            var $season = $('#season_id');
            var $title = $('#title');
            var $icon = $('#icon_path');
            var $base = $('#base_points');
            var $mult = $('#multiplier');
            var $final = $('#final_points');

            function calculate() {
                setTimeout(function() {
                    var tId = $type.val();
                    var lId = $league.val();
                    var sId = $season.val();

                    if (tId && lId && sId) {
                        var t = types.find(function(x) { return x[0] == tId; });
                        var l = leagues.find(function(x) { return x[0] == lId; });
                        var s = seasons.find(function(x) { return x[0] == sId; });

                        if (t && l && s) {
                            // 1. Title
                            $title.val(t[1] + ' ' + l[1] + ' ' + s[1]);
                            // 2. Icon
                            var iconUrl = t[5] || ('/static/img/cups/' + t[2].toLowerCase() + '.svg');
                            $icon.val(iconUrl);
                            // 3. Points
                            var isL1 = (l[2] === '1'); 
                            var base = isL1 ? t[3] : t[4];
                            var mult = s[3];
                            $base.val(base);
                            $mult.val(mult);
                            $final.val((base * mult).toFixed(2));
                        }
                    }
                }, 100);
            }

            $type.on('select2:select change', calculate);
            $league.on('select2:select change', calculate);
            $season.on('select2:select change', calculate);

            // Initial calculation
            if ($type.val() && $league.val() && $season.val()) {
                calculate();
            }
        }
    };
})(window, jQuery);
