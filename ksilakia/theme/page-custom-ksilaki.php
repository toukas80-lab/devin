<?php
/**
 * Custom skewer configurator (quote request).
 */
get_header();
?>
<div class="container page-wrap configurator-page">
<?php while ( have_posts() ) : the_post(); ?>
  <h1 class="page-title"><?php the_title(); ?></h1>
  <div class="entry-content narrow-text"><?php the_content(); ?></div>
<?php endwhile; ?>

  <form class="configurator" id="ksilakia-configurator" method="post" enctype="multipart/form-data" novalidate>
    <input type="text" name="website" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">

    <div class="cfg-preview">
      <div class="cfg-canvas-wrap">
        <canvas id="cfg-canvas-full" width="1200" height="220" aria-label="Προεπισκόπηση ολόκληρου ξυλακιού"></canvas>
        <p class="cfg-caption">Ολόκληρο ξυλάκι — <span id="cfg-dim-label"></span></p>
      </div>
      <div class="cfg-canvas-wrap">
        <canvas id="cfg-canvas-zoom" width="1200" height="320" aria-label="Μεγέθυνση περιοχής λογοτύπου"></canvas>
        <p class="cfg-caption" id="cfg-zoom-caption">Μεγέθυνση (ενδεικτική απόδοση)</p>
      </div>
    </div>

    <div class="cfg-grid">
      <fieldset class="cfg-block">
        <legend>1. Τύπος ξυλακιού</legend>
        <div class="cfg-types">
          <label class="cfg-type"><input type="radio" name="stick_type" value="round" checked> <span><strong>Κανονικό ξυλάκι</strong><small>Στρογγυλό, χάραξη laser κατά μήκος</small></span></label>
          <label class="cfg-type"><input type="radio" name="stick_type" value="paddle"> <span><strong>Καλαμάκι κουπί</strong><small>Πλατύ άκρο (κουπί) για το λογότυπο</small></span></label>
        </div>
      </fieldset>

      <fieldset class="cfg-block">
        <legend>2. Διαστάσεις (mm)</legend>
        <div class="cfg-fields">
          <label>Μήκος <span class="required">*</span><input type="number" name="length" value="215" min="80" max="300" step="1" required></label>
          <label>Διάμετρος <span class="required">*</span><input type="number" name="diameter" value="4" min="2" max="5" step="0.1" required></label>
          <label>Μύτη
            <select name="point">
              <option value="sharp">Αιχμηρή (Point)</option>
              <option value="blunt">Χωρίς μύτη (Blunt point)</option>
            </select>
          </label>
        </div>
        <p class="cfg-hint">Μέγιστο: μήκος 300 mm, διάμετρος 5 mm. Συνήθεις διαστάσεις: 215×3,2 · 215×4 · 240×4 mm.</p>
      </fieldset>

      <fieldset class="cfg-block">
        <legend>3. Λογότυπο / σήμανση <small class="cfg-optional">(προαιρετικό)</small></legend>
        <div class="cfg-tabs" role="tablist">
          <label class="cfg-tab"><input type="radio" name="logo_mode" value="none" checked> Χωρίς λογότυπο</label>
          <label class="cfg-tab"><input type="radio" name="logo_mode" value="text"> Κείμενο</label>
          <label class="cfg-tab"><input type="radio" name="logo_mode" value="image"> Εικόνα / φωτογραφία</label>
        </div>
        <p class="cfg-hint cfg-mode cfg-mode-none">Απλό ξυλάκι χωρίς χάραξη. Αν θέλετε το όνομα ή το λογότυπό σας, επιλέξτε «Κείμενο» ή «Εικόνα / φωτογραφία».</p>
        <div class="cfg-mode cfg-mode-text" hidden>
          <label>Κείμενο <span class="required">*</span><input type="text" name="logo_text" maxlength="40" placeholder="π.χ. CRAZYSOUVLE" autocomplete="organization"></label>
          <label>Γραμματοσειρά
            <select name="logo_font">
              <option value="sans">Απλή (sans-serif)</option>
              <option value="serif">Κλασική (serif)</option>
              <option value="mono">Μονοδιάστατη (mono)</option>
              <option value="black">Έντονη (black)</option>
            </select>
          </label>
        </div>
        <div class="cfg-mode cfg-mode-image" hidden>
          <label class="cfg-file">Αρχείο λογοτύπου ή φωτογραφία <span class="required">*</span>
            <input type="file" name="logo_file" accept="image/png,image/jpeg,image/webp">
            <small>PNG/JPG/WebP έως 8 MB. Ιδανικά σκούρο λογότυπο σε λευκό φόντο — το λευκό φόντο αφαιρείται αυτόματα.</small>
          </label>
          <div class="cfg-crop" hidden>
            <p class="cfg-subtitle">Περικοπή εικόνας</p>
            <div class="cfg-crop-stage"><canvas id="cfg-crop-canvas" width="480" height="300"></canvas></div>
            <div class="cfg-sliders">
              <label>Αριστερά <input type="range" name="crop_left" min="0" max="90" value="0"></label>
              <label>Δεξιά <input type="range" name="crop_right" min="0" max="90" value="0"></label>
              <label>Πάνω <input type="range" name="crop_top" min="0" max="90" value="0"></label>
              <label>Κάτω <input type="range" name="crop_bottom" min="0" max="90" value="0"></label>
              <label>Ένταση χάραξης <input type="range" name="burn" min="20" max="100" value="60"></label>
            </div>
          </div>
        </div>
      </fieldset>

      <fieldset class="cfg-block">
        <legend>4. Ποσότητα</legend>
        <label>Παλέτες <span class="required">*</span><input type="number" name="pallets" value="1" min="1" max="100" step="1" required></label>
        <p class="cfg-hint">Ελάχιστη παραγγελία για custom ξυλάκι: 1 παλέτα. Τεμάχια ανά παλέτα και τιμή δίνονται με την προσφορά.</p>
      </fieldset>

      <fieldset class="cfg-block cfg-contact">
        <legend>5. Στοιχεία επικοινωνίας</legend>
        <div class="cfg-fields">
          <label>Όνομα / Επιχείρηση <span class="required">*</span><input type="text" name="name" required autocomplete="name"></label>
          <label>Τηλέφωνο <span class="required">*</span><input type="tel" name="phone" required autocomplete="tel"></label>
          <label>Email <span class="required">*</span><input type="email" name="email" required autocomplete="email"></label>
          <label>ΑΦΜ (προαιρετικό)<input type="text" name="afm" inputmode="numeric" maxlength="9"></label>
        </div>
        <label>Σχόλια<textarea name="notes" rows="3" placeholder="π.χ. χρήση σε μηχανή SM7000, επιθυμητός χρόνος παράδοσης"></textarea></label>
        <button type="submit" class="btn">Αποστολή αιτήματος προσφοράς</button>
        <p class="form-msg" role="status"></p>
        <p class="cfg-hint">Θα λάβουμε το σχέδιό σας με το λογότυπο και θα σας απαντήσουμε με προσφορά. Δεν γίνεται πληρωμή online.</p>
      </fieldset>
    </div>
  </form>
</div>
<?php get_footer(); ?>
