<?php
/**
 * Homepage.
 */
get_header();
$img = get_template_directory_uri() . '/img/';
?>
<section class="hero" id="top">
  <div class="container hero-grid">
    <div class="hero-text">
      <p class="eyebrow">Επίσημη διάθεση <a href="https://www.vnsrl.com/" target="_blank" rel="noopener" style="color:inherit">VN srl</a> στην Ελλάδα</p>
      <h1>Καλαμάκια για σουβλάκια<br>bamboo επαγγελματικής ποιότητας</h1>
      <p class="lead">Τα ίδια ξυλάκια που φτιάχνει η <a href="https://www.vnsrl.com/" target="_blank" rel="noopener">VN srl</a> για τις σουβλακομηχανές της: ίσια, ίδια διάμετρος σε κάθε τεμάχιο, χωρίς χημικά, με CE. Δουλεύουν το ίδιο καλά στο χέρι και στη μηχανή. Παραγγέλνετε online σακούλα των 1.000 ή κούτα των 10.000, σε τιμή λιανικής ή χονδρικής αν έχετε επιχείρηση.</p>
      <div class="hero-cta">
        <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>" class="btn">Δείτε τα προϊόντα</a>
        <a href="<?php echo esc_url( ksilakia_page_url( 'xondriki-b2b' ) ); ?>" class="btn btn-outline">Τιμές χονδρικής B2B</a>
      </div>
      <ul class="hero-badges">
        <li>Πιστοποίηση CE</li>
        <li>Χωρίς χημικά πρόσθετα</li>
        <li>Ιχνηλασιμότητα παρτίδας</li>
        <li>Συσκευασία MAP</li>
      </ul>
    </div>
    <div class="hero-img">
      <img src="<?php echo esc_url( $img . 'pack-closeup.jpg' ); ?>" alt="Καλαμάκια για σουβλάκια bamboo VN — σακούλα 1.000 τεμαχίων" width="1600" height="739" fetchpriority="high">
    </div>
  </div>
</section>

<section class="products" id="proionta">
  <div class="container">
    <h2>Καλαμάκια για σουβλάκια σε 3 διαστάσεις</h2>
    <p class="section-lead">Λεπτό 215×3,2 για το κλασικό καλαμάκι, 215×4 για πιο βαρύ σουβλάκι ή μηχανή, 240×4 όταν θέλετε μεγαλύτερη μερίδα. Όλα από γιγάντιο bamboo «Mao» της <a href="https://www.vnsrl.com/" target="_blank" rel="noopener">VN srl</a>, με αιχμηρή μύτη. Σακούλα 1.000 τεμ. ή κούτα 10.000 τεμ. (10 σακούλες).</p>
    <?php echo do_shortcode( '[products limit="3" columns="3" orderby="menu_order" order="ASC"]' ); ?>
    <p class="note">Χρειάζεστε άλλη διάσταση, μύτη ή το λογότυπό σας στο ξυλάκι; <a href="<?php echo esc_url( ksilakia_page_url( 'custom-ksilaki' ) ); ?>">Φτιάξε το ξυλάκι σου</a>.</p>
  </div>
</section>

<section class="quality" id="poiotita">
  <div class="container quality-grid">
    <div>
      <h2>Γιατί καλαμάκια σουβλακιού VN</h2>
      <ul class="checks">
        <li><strong>Ίδια διάμετρος σε όλα.</strong> Η VN φτιάχνει σουβλακομηχανές, οπότε ξέρει τι παθαίνει μια μηχανή όταν ένα ξυλάκι είναι μισό χιλιοστό πιο χοντρό. Τα καλαμάκια της βγαίνουν στη διάσταση που γράφει η σακούλα.</li>
        <li><strong>CE για επαφή με τρόφιμα.</strong> Καλύπτουν τα ευρωπαϊκά και τα καναδικά πρότυπα υγιεινής. Χρήσιμο και στον έλεγχο του ΕΦΕΤ.</li>
        <li><strong>Χωρίς λευκαντικά και χημικά.</strong> Το bamboo δεν ασπρίζεται τεχνητά. Τυχαία δείγματα πηγαίνουν τακτικά σε εργαστήριο.</li>
        <li><strong>Αριθμός παρτίδας.</strong> Κάθε σακούλα έχει lot number, οπότε ξέρετε από ποια παραγωγή είναι ό,τι χρησιμοποιείτε.</li>
        <li><strong>Συσκευασία MAP.</strong> Στην κούτα, οι δέκα σακούλες κλείνονται μαζί σε σακούλα τροποποιημένης ατμόσφαιρας. Δεν πιάνουν υγρασία, δεν μουχλιάζουν, δεν φουσκώνουν.</li>
        <li><strong>Bamboo «Mao».</strong> Γιγάντιο bamboo από τη ΒΑ Ασία που ξαναφυτρώνει μόνο του και κόβεται σύμφωνα με τους τοπικούς κανόνες.</li>
      </ul>
    </div>
    <div class="quality-side">
      <img src="<?php echo esc_url( $img . 'box-215-4.jpg' ); ?>" alt="Κούτα 10.000 καλαμάκια για σουβλάκια VN 215×4 mm SSP (10 σακούλες των 1.000)" width="1600" height="740" loading="lazy">
      <div class="cert">
        <img src="<?php echo esc_url( $img . 'bamboo-cert.png' ); ?>" alt="Πιστοποίηση CE καλαμάκια σουβλακιού VN" width="262" height="64" loading="lazy">
        <p>Παραγωγός: <a href="https://www.vnsrl.com/" rel="noopener" target="_blank">VN srl</a>, Ιταλία — κατασκευαστής των μηχανών σουβλακιών SM3000 & SM7000. Διάθεση Ελλάδας: <a href="https://crazysouvle.gr" rel="noopener">Crazy Souvle</a>.</p>
      </div>
    </div>
  </div>
</section>

<section class="b2b" id="b2b">
  <div class="container b2b-grid">
    <div>
      <h2>Χονδρική για επαγγελματίες (B2B)</h2>
      <p>Έχετε ψητοπωλείο, κρεοπωλείο, βιοτεχνία ή catering; Ανοίξτε λογαριασμό B2B και βλέπετε τις τιμές χονδρικής απευθείας στο site, για κούτα ή παλέτα, με τιμολόγιο.</p>
      <ol>
        <li>Εγγραφή με επωνυμία & ΑΦΜ</li>
        <li>Έγκριση εντός 1 εργάσιμης</li>
        <li>Τιμές χονδρικής & παραγγελία online</li>
      </ol>
      <a href="<?php echo esc_url( add_query_arg( 'b2b', '1', wc_get_page_permalink( 'myaccount' ) ) ); ?>" class="btn">Εγγραφή B2B</a>
    </div>
    <img src="<?php echo esc_url( $img . 'pallet-215-32.jpg' ); ?>" alt="Παλέτα με κούτες καλαμάκια για σουβλάκια VN 215×3,2 mm — χονδρική" width="739" height="1600" loading="lazy" style="border-radius:14px;max-height:420px;width:100%;object-fit:cover">
  </div>
</section>

<section class="for-who">
  <div class="container">
    <h2>Για ποιους</h2>
    <div class="who-grid">
      <div><h3>Ψητοπωλεία & σουβλατζίδικα</h3><p>Καθημερινή κατανάλωση σε κούτες, με τιμή χονδρικής και ξυλάκι που δεν σπάει στο πέρασμα.</p></div>
      <div><h3>Κρεοπωλεία</h3><p>Για τα σουβλάκια της βιτρίνας. Ίδιο μήκος σε όλα, ωραίο μάτι στο ψυγείο.</p></div>
      <div><h3>Βιοτεχνίες κρέατος</h3><p>Για μηχανή. Διαλέγετε τη διάμετρο που δέχεται η μήτρα σας και δεν ασχολείστε ξανά με εμπλοκές από ξυλάκι.</p></div>
      <div><h3>Catering & σπίτι</h3><p>Μια σακούλα των 1.000 φτάνει για αρκετά τραπέζια ή για όλο το καλοκαίρι στη σχάρα. Η κούτα βγαίνει πιο φθηνά το τεμάχιο.</p></div>
    </div>
  </div>
</section>

<section class="machines" id="souvlakomixanes">
  <div class="container narrow">
    <h2>Μηχανές για σουβλάκια & καλαμάκια από την ίδια πηγή</h2>
    <p>Τις <a href="https://crazysouvle.gr" rel="noopener">σουβλακομηχανές VN SM3000 και SM7000</a> τις φέρνουμε στην Ελλάδα εμείς, μέσω του <a href="https://crazysouvle.gr" rel="noopener">crazysouvle.gr</a>. Εκεί θα βρείτε τις <a href="https://crazysouvle.gr" rel="noopener">μηχανές για σουβλάκια</a>, ανταλλακτικά και σέρβις. Τα καλαμάκια είναι το άλλο μισό της ίδιας δουλειάς: όταν βγαίνουν από το ίδιο εργοστάσιο με τη μηχανή, απλώς δεν κολλάνε.</p>
  </div>
</section>

<section class="faq" id="faq">
  <div class="container narrow">
    <h2>Συχνές ερωτήσεις για τα καλαμάκια σουβλακιού</h2>
    <?php foreach ( ksilakia_faq() as $i => $q ) : ?>
      <details <?php echo 0 === $i ? 'open' : ''; ?>><summary><?php echo esc_html( $q[0] ); ?></summary><p><?php echo str_replace( array( 'VN srl', 'crazysouvle.gr' ), array( '<a href="https://www.vnsrl.com/" target="_blank" rel="noopener">VN srl</a>', '<a href="https://crazysouvle.gr" rel="noopener">crazysouvle.gr</a>' ), esc_html( $q[1] ) ); ?></p></details>
    <?php endforeach; ?>
  </div>
</section>

<?php get_template_part( 'parts/contact' ); ?>
<?php get_footer(); ?>
