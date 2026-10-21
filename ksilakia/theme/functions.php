<?php
/**
 * Ksilakia theme functions: setup, WooCommerce support, B2B registration, contact form, SEO.
 */

defined( 'ABSPATH' ) || exit;

define( 'KSILAKIA_PHONE', '+302310227642' );
define( 'KSILAKIA_PHONE_DISPLAY', '+30 2310 227642' );
define( 'KSILAKIA_WHATSAPP', '306947806591' );
define( 'KSILAKIA_WHATSAPP_DISPLAY', '+30 6947 806591' );
define( 'KSILAKIA_GA4_ID', 'G-3D7K7BPTK0' );
define( 'KSILAKIA_EMAIL', 'info@ksilakia.gr' );
define( 'KSILAKIA_ADDRESS', 'Μακεδονικού Αγώνα 19, Παλαιόκαστρο 570 13, Θεσσαλονίκη' );
define( 'KSILAKIA_MAPS', 'https://maps.app.goo.gl/AxyGsBF8LFyQ1tY78' );
define( 'KSILAKIA_COMPANY', 'Φουντούκας Θεόδωρος Μον. ΙΚΕ' );

/* ---------------------------------------------------------------- setup */

add_action( 'after_setup_theme', function () {
	add_theme_support( 'title-tag' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'html5', array( 'search-form', 'gallery', 'caption', 'style', 'script' ) );
	add_theme_support( 'woocommerce', array( 'product_grid' => array( 'default_columns' => 3, 'min_columns' => 1, 'max_columns' => 4 ) ) );
	add_filter( 'single_product_archive_thumbnail_size', function () { return 'woocommerce_single'; } );
	add_theme_support( 'wc-product-gallery-zoom' );
	add_theme_support( 'wc-product-gallery-lightbox' );
	add_theme_support( 'wc-product-gallery-slider' );
	register_nav_menus( array( 'primary' => 'Κύριο μενού', 'footer' => 'Μενού υποσέλιδου' ) );
} );

add_action( 'wp_enqueue_scripts', function () {
	wp_enqueue_style( 'ksilakia', get_stylesheet_uri(), array(), wp_get_theme()->get( 'Version' ) );
	wp_enqueue_script( 'ksilakia', get_template_directory_uri() . '/js/main.js', array(), wp_get_theme()->get( 'Version' ), true );
	wp_localize_script( 'ksilakia', 'ksilakia', array(
		'ajax'      => admin_url( 'admin-ajax.php' ),
		'nonce'     => wp_create_nonce( 'ksilakia_contact' ),
		'afm_nonce' => wp_create_nonce( 'ksilakia_afm' ),
		'quote_nonce' => wp_create_nonce( 'ksilakia_custom_quote' ),
	) );
	if ( is_page( 'custom-ksilaki' ) ) {
		wp_enqueue_script( 'ksilakia-configurator', get_template_directory_uri() . '/js/configurator.js', array( 'ksilakia' ), wp_get_theme()->get( 'Version' ), true );
	}
} );

/* ---------- Custom skewer configurator: quote requests ---------- */
add_action( 'init', function () {
	register_post_type( 'ksilakia_quote', array(
		'labels'          => array(
			'name'          => 'Αιτήματα custom',
			'singular_name' => 'Αίτημα custom',
			'menu_name'     => 'Αιτήματα custom',
			'edit_item'     => 'Αίτημα custom ξυλακιού',
			'search_items'  => 'Αναζήτηση αιτημάτων',
			'not_found'     => 'Δεν υπάρχουν αιτήματα.',
		),
		'public'          => false,
		'show_ui'         => true,
		'show_in_menu'    => true,
		'menu_icon'       => 'dashicons-art',
		'menu_position'   => 57,
		'supports'        => array( 'title' ),
		'capability_type' => 'post',
		'capabilities'    => array( 'create_posts' => 'do_not_allow' ),
		'map_meta_cap'    => true,
	) );
} );

add_filter( 'manage_ksilakia_quote_posts_columns', function ( $cols ) {
	return array(
		'cb'       => $cols['cb'],
		'title'    => 'Πελάτης',
		'kq_spec'  => 'Ξυλάκι',
		'kq_qty'   => 'Παλέτες',
		'kq_phone' => 'Τηλέφωνο',
		'kq_mail'  => 'Email αποστολή',
		'date'     => 'Ημερομηνία',
	);
} );
add_action( 'manage_ksilakia_quote_posts_custom_column', function ( $col, $id ) {
	$c = get_post_meta( $id, 'config', true );
	switch ( $col ) {
		case 'kq_spec':
			echo esc_html( ksilakia_quote_spec( $c ) );
			break;
		case 'kq_qty':
			echo (int) ( $c['pallets'] ?? 0 );
			break;
		case 'kq_phone':
			echo esc_html( get_post_meta( $id, 'phone', true ) );
			break;
		case 'kq_mail':
			echo get_post_meta( $id, 'mail_sent', true ) ? 'ΟΚ' : '<strong style="color:#b32d2e">Απέτυχε</strong>';
			break;
	}
}, 10, 2 );

function ksilakia_quote_spec( $c ) {
	if ( ! is_array( $c ) ) {
		return '';
	}
	$s = ( 'paddle' === $c['type'] ? 'Κουπί' : 'Κανονικό' ) . ' ' . $c['length'] . ' × ' . $c['diameter'] . ' mm';
	if ( 'paddle' === $c['type'] ) {
		$s .= ', κουπί ' . $c['paddleLength'] . ' × ' . $c['paddleWidth'] . ' mm';
	}
	return $s . ( 'sharp' === $c['point'] ? ', αιχμηρή μύτη' : ', χωρίς μύτη' );
}

function ksilakia_quote_summary( $id ) {
	$c     = get_post_meta( $id, 'config', true );
	$lines = array(
		'Όνομα/Επιχείρηση: ' . get_post_meta( $id, 'name', true ),
		'Τηλέφωνο: ' . get_post_meta( $id, 'phone', true ),
		'Email: ' . get_post_meta( $id, 'email', true ),
		'ΑΦΜ: ' . get_post_meta( $id, 'afm', true ),
		'',
		'Ξυλάκι: ' . ksilakia_quote_spec( $c ),
		'Ποσότητα: ' . (int) $c['pallets'] . ' παλέτα/ες',
		'Σήμανση: ' . ( 'none' === $c['mode'] ? 'χωρίς λογότυπο' : ( 'image' === $c['mode'] ? 'εικόνα/λογότυπο (συνημμένο)' : 'κείμενο «' . $c['text'] . '» (γραμματοσειρά: ' . $c['font'] . ')' ) ),
		'',
		'Σχόλια: ' . get_post_meta( $id, 'notes', true ),
	);
	return implode( "\n", $lines );
}

add_action( 'edit_form_after_title', function ( $post ) {
	if ( 'ksilakia_quote' !== $post->post_type ) {
		return;
	}
	echo '<div style="background:#fff;border:1px solid #c3c4c7;padding:16px;margin-top:16px"><pre style="white-space:pre-wrap;font-size:14px;margin:0">' . esc_html( ksilakia_quote_summary( $post->ID ) ) . '</pre>';
	foreach ( array( 'preview_id' => 'Προεπισκόπηση', 'logo_id' => 'Αρχείο λογοτύπου' ) as $key => $label ) {
		$att = (int) get_post_meta( $post->ID, $key, true );
		if ( $att && ( $url = wp_get_attachment_url( $att ) ) ) {
			echo '<p><strong>' . $label . ':</strong> <a href="' . esc_url( $url ) . '" target="_blank">' . esc_html( basename( $url ) ) . '</a></p>';
			if ( 'preview_id' === $key ) {
				echo '<img src="' . esc_url( $url ) . '" style="max-width:100%;border:1px solid #ddd" alt="">';
			}
		}
	}
	echo '</div>';
} );

add_action( 'wp_ajax_ksilakia_custom_quote', 'ksilakia_custom_quote_handler' );
add_action( 'wp_ajax_nopriv_ksilakia_custom_quote', 'ksilakia_custom_quote_handler' );

function ksilakia_custom_quote_handler() {
	check_ajax_referer( 'ksilakia_custom_quote', 'nonce' );
	if ( ! empty( $_POST['website'] ) ) {
		wp_send_json( array( 'ok' => true, 'id' => 0 ) );
	}
	$fail = function ( $m ) {
		wp_send_json( array( 'ok' => false, 'error' => $m ) );
	};
	$name  = sanitize_text_field( wp_unslash( $_POST['name'] ?? '' ) );
	$phone = sanitize_text_field( wp_unslash( $_POST['phone'] ?? '' ) );
	$email = sanitize_email( wp_unslash( $_POST['email'] ?? '' ) );
	$afm   = preg_replace( '/\D/', '', (string) ( $_POST['afm'] ?? '' ) );
	$notes = sanitize_textarea_field( wp_unslash( $_POST['notes'] ?? '' ) );
	if ( ! $name || ! $phone || ! is_email( $email ) ) {
		$fail( 'Συμπληρώστε όνομα, τηλέφωνο και έγκυρο email.' );
	}
	$raw = json_decode( wp_unslash( $_POST['config'] ?? '' ), true );
	if ( ! is_array( $raw ) ) {
		$fail( 'Μη έγκυρη διαμόρφωση.' );
	}
	$range = function ( $v, $min, $max ) {
		$v = (float) $v;
		return $v >= $min && $v <= $max ? $v : null;
	};
	$c = array(
		'type'         => in_array( $raw['type'] ?? '', array( 'round', 'paddle' ), true ) ? $raw['type'] : null,
		'length'       => $range( $raw['length'] ?? 0, 80, 300 ),
		'diameter'     => $range( $raw['diameter'] ?? 0, 2, 5 ),
		'paddleWidth'  => 10,
		'paddleLength' => 'paddle' === ( $raw['type'] ?? '' ) ? 40 : 0,
		'point'        => in_array( $raw['point'] ?? '', array( 'sharp', 'blunt' ), true ) ? $raw['point'] : null,
		'mode'         => in_array( $raw['mode'] ?? '', array( 'none', 'text', 'image' ), true ) ? $raw['mode'] : null,
		'text'         => sanitize_text_field( mb_substr( (string) ( $raw['text'] ?? '' ), 0, 40 ) ),
		'font'         => in_array( $raw['font'] ?? '', array( 'sans', 'serif', 'mono', 'black' ), true ) ? $raw['font'] : 'sans',
		'pallets'      => (int) ( $raw['pallets'] ?? 0 ),
	);
	if ( in_array( null, $c, true ) ) {
		$fail( 'Μη έγκυρες διαστάσεις ή επιλογές.' );
	}
	if ( $c['pallets'] < 1 || $c['pallets'] > 100 || $c['pallets'] !== (int) ( $_POST['pallets'] ?? 0 ) ) {
		$fail( 'Η ελάχιστη ποσότητα είναι 1 παλέτα (ακέραιος αριθμός παλετών).' );
	}
	if ( 'text' === $c['mode'] && '' === $c['text'] ) {
		$fail( 'Γράψτε το κείμενο για τη χάραξη.' );
	}
	if ( 'image' === $c['mode'] && empty( $_FILES['logo_file']['tmp_name'] ) ) {
		$fail( 'Ανεβάστε το λογότυπό σας.' );
	}

	require_once ABSPATH . 'wp-admin/includes/file.php';
	require_once ABSPATH . 'wp-admin/includes/media.php';
	require_once ABSPATH . 'wp-admin/includes/image.php';
	$allowed = array( 'png' => 'image/png', 'jpg|jpeg' => 'image/jpeg', 'webp' => 'image/webp' );
	$upload  = function ( $field, $parent, $max ) use ( $allowed, $fail ) {
		if ( empty( $_FILES[ $field ]['tmp_name'] ) ) {
			return 0;
		}
		if ( (int) $_FILES[ $field ]['size'] > $max ) {
			$fail( 'Το αρχείο ξεπερνά τα 8 MB.' );
		}
		$check = wp_check_filetype_and_ext( $_FILES[ $field ]['tmp_name'], $_FILES[ $field ]['name'], $allowed );
		if ( empty( $check['type'] ) || ! @getimagesize( $_FILES[ $field ]['tmp_name'] ) ) {
			$fail( 'Δεκτά μόνο PNG/JPG/WebP.' );
		}
		$id = media_handle_upload( $field, $parent, array( 'post_title' => 'custom-' . $parent . '-' . $field ), array(
			'test_form'                => false,
			'mimes'                    => $allowed,
			'unique_filename_callback' => fn( $dir, $n, $ext ) => 'custom-' . $parent . '-' . wp_generate_password( 10, false ) . $ext,
		) );
		return is_wp_error( $id ) ? 0 : $id;
	};

	$id = wp_insert_post( array(
		'post_type'   => 'ksilakia_quote',
		'post_status' => 'publish',
		'post_title'  => $name . ' — ' . ksilakia_quote_spec( $c ) . ' × ' . $c['pallets'] . ' παλ.',
		'meta_input'  => compact( 'name', 'phone', 'email', 'afm', 'notes' ) + array( 'config' => $c, 'ip' => sanitize_text_field( $_SERVER['REMOTE_ADDR'] ?? '' ) ),
	), true );
	if ( is_wp_error( $id ) ) {
		$fail( 'Δεν έγινε αποθήκευση. Καλέστε μας στο ' . KSILAKIA_PHONE_DISPLAY . '.' );
	}
	$logo_id    = 'image' === $c['mode'] ? $upload( 'logo_file', $id, 8 * MB_IN_BYTES ) : 0;
	$preview_id = $upload( 'preview', $id, 4 * MB_IN_BYTES );
	update_post_meta( $id, 'logo_id', $logo_id );
	update_post_meta( $id, 'preview_id', $preview_id );

	$files = array_filter( array_map( 'get_attached_file', array_filter( array( $preview_id, $logo_id ) ) ) );
	$body  = ksilakia_quote_summary( $id ) . "\n\nΔιαχείριση: " . admin_url( 'post.php?post=' . $id . '&action=edit' );
	$sent  = wp_mail( KSILAKIA_EMAIL, '[ksilakia.gr] Αίτημα custom ξυλακιού #' . $id . ' — ' . $name, $body, array( 'Reply-To: ' . $email ), $files );
	update_post_meta( $id, 'mail_sent', $sent ? 1 : 0 );
	wp_mail( $email, 'Λάβαμε το αίτημά σας για custom ξυλάκι (#' . $id . ')',
		"Ευχαριστούμε! Λάβαμε το αίτημα προσφοράς σας και θα σας απαντήσουμε σύντομα.\n\n" . ksilakia_quote_summary( $id ) . "\n\n" . KSILAKIA_COMPANY . ' · ' . KSILAKIA_PHONE_DISPLAY . ' · ' . KSILAKIA_EMAIL,
		array( 'Reply-To: ' . KSILAKIA_EMAIL ), $preview_id ? array( get_attached_file( $preview_id ) ) : array() );
	wp_send_json( array( 'ok' => true, 'id' => $id ) );
}

add_action( 'wp_print_footer_scripts', function () {
	$scripts = array(
		'wc-ppcp-sdk-v6-boot'               => 'window.wc_ppcp_sdk_v6',
		'wc-ppcp-sdk-v6-add-payment-method' => 'window.wc_ppcp_sdk_v6_save',
		'wc-settings'                     => "window.wcSettings && window.wcSettings.paymentMethodData && window.wcSettings.paymentMethodData['ppcp-sdk-v6']",
	);
	foreach ( $scripts as $handle => $object ) {
		if ( wp_script_is( $handle, 'enqueued' ) ) {
			wp_add_inline_script(
				$handle,
				"(function (config) { if (config && config.locale === 'el') { config.locale = 'el-GR'; } })({$object});",
				'before'
			);
		}
	}
}, 5 );

add_filter( 'body_class', function ( $c ) {
	if ( is_page() ) {
		$c[] = 'page-' . get_post_field( 'post_name' );
	}
	return $c;
} );

add_filter( 'loop_shop_columns', fn() => 3 );
add_filter( 'woocommerce_output_related_products_args', fn( $a ) => array_merge( $a, array( 'posts_per_page' => 3, 'columns' => 3 ) ) );
remove_action( 'woocommerce_before_main_content', 'woocommerce_breadcrumb', 20 );
remove_action( 'woocommerce_sidebar', 'woocommerce_get_sidebar', 10 );
remove_action( 'woocommerce_before_shop_loop', 'woocommerce_catalog_ordering', 30 );
remove_action( 'woocommerce_before_checkout_form', 'woocommerce_checkout_coupon_form', 10 );
add_filter( 'woocommerce_enqueue_styles', fn( $s ) => $s ); // keep default WC styles as base
add_filter( 'woocommerce_attribute', function ( $text, $attribute ) {
	if ( 'Κατασκευαστής' === $attribute->get_name() ) {
		return str_replace( 'VN srl', '<a href="https://www.vnsrl.com/" target="_blank" rel="noopener">VN srl</a>', $text );
	}
	return $text;
}, 10, 2 );

/* ------------------------------------------------------------ helpers */

function ksilakia_logo_svg() {
	return '<svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="12" fill="#c8893b"/><path d="M14 50 L50 14" stroke="#fff5e6" stroke-width="5" stroke-linecap="round"/><path d="M22 50 L50 22" stroke="#fff5e6" stroke-width="5" stroke-linecap="round" opacity=".7"/><path d="M14 42 L42 14" stroke="#fff5e6" stroke-width="5" stroke-linecap="round" opacity=".7"/></svg>';
}

function ksilakia_page_url( $slug ) {
	$p = get_page_by_path( $slug );
	return $p ? get_permalink( $p ) : home_url( '/' . $slug . '/' );
}

function ksilakia_whatsapp_url() {
	return 'https://wa.me/' . KSILAKIA_WHATSAPP;
}

/* ------------------------------------------------------- B2B / χονδρική */

const KSILAKIA_B2B_ROLE = 'wholesale_customer';

function ksilakia_is_b2b( $user_id = 0 ) {
	$u = $user_id ? get_userdata( $user_id ) : wp_get_current_user();
	return $u && in_array( KSILAKIA_B2B_ROLE, (array) $u->roles, true );
}

// Extra fields on My Account registration form.
add_action( 'woocommerce_register_form', function () {
	$v = fn( $k ) => isset( $_POST[ $k ] ) ? esc_attr( wp_unslash( $_POST[ $k ] ) ) : '';
	$submitted = isset( $_POST['register'] );
	$b2b = $submitted ? ! empty( $_POST['ksilakia_b2b'] ) : ( isset( $_GET['b2b'] ) && '1' === $_GET['b2b'] );
	?>
	<p class="registration-required-hint">Τα πεδία με <span class="required" aria-hidden="true">*</span> είναι υποχρεωτικά.</p>
	<fieldset class="b2b-fields" data-registration-submitted="<?php echo $submitted ? 'true' : 'false'; ?>">
		<legend>Επαγγελματίας; (προαιρετικό)</legend>
		<p class="form-row"><label><input type="checkbox" name="ksilakia_b2b" value="1" <?php checked( $b2b ); ?>> Θέλω λογαριασμό <strong>B2B / χονδρικής</strong> (ψητοπωλείο, κρεοπωλείο, βιοτεχνία)</label></p>
		<p class="form-row"><label>ΑΦΜ<span class="required" aria-hidden="true"<?php echo $b2b ? '' : ' hidden'; ?>> *</span><input type="text" class="input-text" id="ksilakia_vat" name="ksilakia_vat" value="<?php echo $v( 'ksilakia_vat' ); ?>" inputmode="numeric" maxlength="9" data-b2b-required <?php echo $b2b ? 'required aria-required="true"' : ''; ?> data-afm-lookup data-afm-map="name:ksilakia_company,doy:ksilakia_doy,address:ksilakia_address"></label><span class="afm-status" aria-live="polite"></span><small class="afm-hint">Γράψτε τα 9 ψηφία και τα στοιχεία της επιχείρησης συμπληρώνονται αυτόματα.</small></p>
		<p class="form-row"><label>Επωνυμία επιχείρησης<span class="required" aria-hidden="true"<?php echo $b2b ? '' : ' hidden'; ?>> *</span><input type="text" class="input-text" id="ksilakia_company" name="ksilakia_company" value="<?php echo $v( 'ksilakia_company' ); ?>" data-b2b-required <?php echo $b2b ? 'required aria-required="true"' : ''; ?>></label></p>
		<p class="form-row"><label>ΔΟΥ<input type="text" class="input-text" name="ksilakia_doy" value="<?php echo $v( 'ksilakia_doy' ); ?>"></label></p>
		<p class="form-row"><label>Διεύθυνση έδρας<input type="text" class="input-text" name="ksilakia_address" value="<?php echo $v( 'ksilakia_address' ); ?>"></label></p>
		<p class="form-row"><label>Τηλέφωνο<span class="required" aria-hidden="true"<?php echo $b2b ? '' : ' hidden'; ?>> *</span><input type="tel" class="input-text" id="ksilakia_phone" name="ksilakia_phone" value="<?php echo $v( 'ksilakia_phone' ); ?>" data-b2b-required <?php echo $b2b ? 'required aria-required="true"' : ''; ?>></label></p>
		<p class="form-row" style="margin:0;font-size:.9rem;color:#6b6259">Οι λογαριασμοί B2B εγκρίνονται χειροκίνητα εντός 1 εργάσιμης. Μετά την έγκριση βλέπετε τιμές χονδρικής και παραγγέλνετε online.</p>
	</fieldset>
	<?php
} );

add_filter( 'woocommerce_registration_errors', function ( $errors ) {
	if ( ! empty( $_POST['ksilakia_b2b'] ) ) {
		if ( empty( $_POST['ksilakia_company'] ) ) {
			$errors->add( 'company', 'Συμπληρώστε την επωνυμία επιχείρησης για λογαριασμό B2B.' );
		}
		$vat = preg_replace( '/\D/', '', $_POST['ksilakia_vat'] ?? '' );
		if ( strlen( $vat ) !== 9 ) {
			$errors->add( 'vat', 'Το ΑΦΜ πρέπει να έχει 9 ψηφία.' );
		}
		if ( empty( $_POST['ksilakia_phone'] ) ) {
			$errors->add( 'phone', 'Συμπληρώστε τηλέφωνο για λογαριασμό B2B.' );
		}
	}
	return $errors;
} );

add_action( 'woocommerce_created_customer', function ( $user_id ) {
	$company = sanitize_text_field( wp_unslash( $_POST['ksilakia_company'] ?? '' ) );
	$vat     = preg_replace( '/\D/', '', $_POST['ksilakia_vat'] ?? '' );
	$phone   = sanitize_text_field( wp_unslash( $_POST['ksilakia_phone'] ?? '' ) );
	$doy     = sanitize_text_field( wp_unslash( $_POST['ksilakia_doy'] ?? '' ) );
	$address = sanitize_text_field( wp_unslash( $_POST['ksilakia_address'] ?? '' ) );
	if ( $company ) {
		update_user_meta( $user_id, 'billing_company', $company );
	}
	if ( $vat ) {
		update_user_meta( $user_id, 'billing_vat', $vat );
	}
	if ( $doy ) {
		update_user_meta( $user_id, 'billing_doy', $doy );
	}
	if ( $address ) {
		update_user_meta( $user_id, 'billing_address_1', $address );
	}
	if ( $company || $vat ) {
		update_user_meta( $user_id, 'billing_invoice_type', 'invoice' );
	}
	if ( $phone ) {
		update_user_meta( $user_id, 'billing_phone', $phone );
	}
	$u = get_userdata( $user_id );
	if ( ! empty( $_POST['ksilakia_b2b'] ) ) {
		update_user_meta( $user_id, 'ksilakia_b2b_status', 'pending' );
		wp_mail(
			get_option( 'admin_email' ),
			'[ksilakia.gr] Νέα αίτηση B2B: ' . $company,
			"Νέα αίτηση λογαριασμού χονδρικής.\n\nΕπωνυμία: $company\nΑΦΜ: $vat\nΔΟΥ: $doy\nΔιεύθυνση: $address\nΤηλέφωνο: $phone\nEmail: {$u->user_email}\n\nΈγκριση: " . admin_url( 'users.php?role=customer&b2b=pending' )
		);
	} else {
		wp_mail(
			get_option( 'admin_email' ),
			'[ksilakia.gr] Νέα εγγραφή πελάτη',
			"Νέα εγγραφή πελάτη στο ksilakia.gr.\n\nEmail: {$u->user_email}\nΌνομα χρήστη: {$u->user_login}\n\nΧρήστες: " . admin_url( 'users.php?role=customer' )
		);
	}
} );

// Approve/revoke from Users list.
add_filter( 'user_row_actions', function ( $actions, $user ) {
	if ( ! current_user_can( 'edit_users' ) ) {
		return $actions;
	}
	$status = get_user_meta( $user->ID, 'ksilakia_b2b_status', true );
	if ( ksilakia_is_b2b( $user->ID ) ) {
		$url = wp_nonce_url( admin_url( 'users.php?ksilakia_b2b=revoke&user=' . $user->ID ), 'ksilakia_b2b_' . $user->ID );
		$actions['ksilakia_b2b'] = '<a href="' . esc_url( $url ) . '">Αφαίρεση B2B</a>';
	} elseif ( in_array( 'customer', (array) $user->roles, true ) ) {
		$url = wp_nonce_url( admin_url( 'users.php?ksilakia_b2b=approve&user=' . $user->ID ), 'ksilakia_b2b_' . $user->ID );
		$actions['ksilakia_b2b'] = '<a href="' . esc_url( $url ) . '" style="color:#2f7d4f;font-weight:600">' . ( 'pending' === $status ? 'Έγκριση B2B (αίτηση)' : 'Κάνε B2B' ) . '</a>';
	}
	return $actions;
}, 10, 2 );

add_action( 'admin_init', function () {
	if ( empty( $_GET['ksilakia_b2b'] ) || empty( $_GET['user'] ) || ! current_user_can( 'edit_users' ) ) {
		return;
	}
	$uid = (int) $_GET['user'];
	check_admin_referer( 'ksilakia_b2b_' . $uid );
	$u = get_userdata( $uid );
	if ( ! $u ) {
		return;
	}
	if ( 'approve' === $_GET['ksilakia_b2b'] ) {
		$u->set_role( KSILAKIA_B2B_ROLE );
		update_user_meta( $uid, 'ksilakia_b2b_status', 'approved' );
		wp_mail(
			$u->user_email,
			'Ο λογαριασμός B2B σας στο ksilakia.gr εγκρίθηκε',
			"Καλώς ήρθατε!\n\nΟ λογαριασμός χονδρικής σας εγκρίθηκε. Συνδεθείτε για να δείτε τις τιμές χονδρικής και να παραγγείλετε:\n" . wc_get_page_permalink( 'myaccount' ) . "\n\nΤηλ. " . KSILAKIA_PHONE_DISPLAY . "\n" . KSILAKIA_COMPANY
		);
	} else {
		$u->set_role( 'customer' );
		update_user_meta( $uid, 'ksilakia_b2b_status', 'revoked' );
	}
	wp_safe_redirect( remove_query_arg( array( 'ksilakia_b2b', 'user', '_wpnonce' ) ) );
	exit;
} );

// Users list: filter pending B2B + column.
add_action( 'pre_get_users', function ( $q ) {
	if ( is_admin() && ! empty( $_GET['b2b'] ) && 'pending' === $_GET['b2b'] ) {
		$q->set( 'meta_key', 'ksilakia_b2b_status' );
		$q->set( 'meta_value', 'pending' );
	}
} );
add_filter( 'manage_users_columns', fn( $c ) => $c + array( 'ksilakia_b2b' => 'B2B' ) );
add_filter( 'manage_users_custom_column', function ( $out, $col, $uid ) {
	if ( 'ksilakia_b2b' !== $col ) {
		return $out;
	}
	if ( ksilakia_is_b2b( $uid ) ) {
		return '<span style="color:#2f7d4f;font-weight:700">Χονδρική</span>';
	}
	$s = get_user_meta( $uid, 'ksilakia_b2b_status', true );
	$c = get_user_meta( $uid, 'billing_company', true );
	$v = get_user_meta( $uid, 'billing_vat', true );
	return 'pending' === $s ? '<span style="color:#b3261e;font-weight:700">Αίτηση</span><br>' . esc_html( "$c · ΑΦΜ $v" ) : '—';
}, 10, 3 );

// Dashboard note for B2B customers.
add_action( 'woocommerce_account_dashboard', function () {
	$s = get_user_meta( get_current_user_id(), 'ksilakia_b2b_status', true );
	if ( ksilakia_is_b2b() ) {
		echo '<div class="b2b-status approved"><strong>Λογαριασμός χονδρικής ενεργός.</strong> Βλέπετε τιμές B2B σε όλα τα προϊόντα.</div>';
	} elseif ( 'pending' === $s ) {
		echo '<div class="b2b-status"><strong>Η αίτησή σας για λογαριασμό B2B εξετάζεται.</strong> Θα ενημερωθείτε με email μόλις εγκριθεί (συνήθως εντός 1 εργάσιμης).</div>';
	}
}, 5 );

/* ------------------------------------------ ΑΦΜ lookup (VIES / ΑΑΔΕ) */

/**
 * Looks up a Greek ΑΦΜ. Uses the AADE public registry (rgWsPublic2) when
 * KSILAKIA_AADE_USER / KSILAKIA_AADE_PASS are defined in wp-config.php
 * (returns ΔΟΥ + activity), otherwise the credential-free EU VIES REST API
 * (name + address only). Results are cached for 7 days.
 *
 * @return array{name:string,address:string,postcode:string,city:string,doy:string,activity:string,source:string}|WP_Error
 */
function ksilakia_afm_lookup( $afm ) {
	$afm = preg_replace( '/\D/', '', (string) $afm );
	if ( 9 !== strlen( $afm ) || ! ksilakia_afm_checksum( $afm ) ) {
		return new WP_Error( 'invalid', 'Μη έγκυρο ΑΦΜ.' );
	}
	$key    = 'ksilakia_afm_' . $afm;
	$cached = get_transient( $key );
	if ( is_array( $cached ) ) {
		return $cached;
	}
	$data = null;
	if ( defined( 'KSILAKIA_AADE_USER' ) && defined( 'KSILAKIA_AADE_PASS' ) ) {
		$data = ksilakia_afm_lookup_aade( $afm );
	}
	if ( ! is_array( $data ) ) {
		$data = ksilakia_afm_lookup_vies( $afm );
	}
	if ( is_wp_error( $data ) ) {
		return $data;
	}
	set_transient( $key, $data, 7 * DAY_IN_SECONDS );
	return $data;
}

function ksilakia_afm_checksum( $afm ) {
	$sum = 0;
	for ( $i = 0; $i < 8; $i++ ) {
		$sum += (int) $afm[ $i ] * ( 2 ** ( 8 - $i ) );
	}
	return ( $sum % 11 ) % 10 === (int) $afm[8];
}

function ksilakia_afm_lookup_vies( $afm ) {
	// VIES drops the TLS session without close_notify when compression is combined with Connection: close.
	$r = wp_remote_get( 'https://ec.europa.eu/taxation_customs/vies/rest-api/ms/EL/vat/' . $afm, array(
		'timeout'    => 12,
		'decompress' => false,
		'headers'    => array( 'Accept-Encoding' => 'identity', 'Accept' => 'application/json' ),
	) );
	if ( is_wp_error( $r ) ) {
		return new WP_Error( 'net', 'Η υπηρεσία VIES δεν απαντά. Συμπληρώστε τα στοιχεία χειροκίνητα.' );
	}
	$j = json_decode( wp_remote_retrieve_body( $r ), true );
	if ( ! is_array( $j ) || empty( $j['isValid'] ) ) {
		if ( is_array( $j ) && ! empty( $j['userError'] ) && 'VALID' !== $j['userError'] && 'INVALID' !== $j['userError'] ) {
			return new WP_Error( 'net', 'Η υπηρεσία VIES είναι προσωρινά μη διαθέσιμη. Συμπληρώστε τα στοιχεία χειροκίνητα.' );
		}
		return new WP_Error( 'notfound', 'Δεν βρέθηκε στο μητρώο VIES. Συμπληρώστε τα στοιχεία χειροκίνητα.' );
	}
	$addr = trim( preg_replace( '/\s+/', ' ', (string) ( $j['address'] ?? '' ) ) );
	$name = trim( explode( '||', (string) ( $j['name'] ?? '' ) )[0] ); // VIES: "legal name||trade name"
	$out  = array( 'name' => $name, 'address' => $addr, 'postcode' => '', 'city' => '', 'doy' => '', 'activity' => '', 'source' => 'VIES' );
	// VIES format: "ΟΔΟΣ 12 10559 - ΑΘΗΝΑ"
	if ( preg_match( '/^(.*?)\s*(\d{3}\s?\d{2})\s*-\s*(.+)$/u', $addr, $m ) ) {
		$out['address']  = trim( $m[1] );
		$out['postcode'] = str_replace( ' ', '', $m[2] );
		$out['city']     = trim( $m[3] );
	}
	return $out;
}

function ksilakia_afm_lookup_aade( $afm ) {
	$env = '<?xml version="1.0" encoding="UTF-8"?><env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope" xmlns:ns1="http://rgwspublic2/RgWsPublic2Service" xmlns:ns2="http://rgwspublic2/RgWsPublic2" xmlns:ns3="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">'
		. '<env:Header><ns3:Security><ns3:UsernameToken><ns3:Username>' . esc_html( KSILAKIA_AADE_USER ) . '</ns3:Username><ns3:Password>' . esc_html( KSILAKIA_AADE_PASS ) . '</ns3:Password></ns3:UsernameToken></ns3:Security></env:Header>'
		. '<env:Body><ns1:rgWsPublic2AfmMethod><ns1:INPUT_REC><ns2:afm_called_by/><ns2:afm_called_for>' . $afm . '</ns2:afm_called_for></ns1:INPUT_REC></ns1:rgWsPublic2AfmMethod></env:Body></env:Envelope>';
	$r   = wp_remote_post( 'https://www1.gsis.gr/wsaade/RgWsPublic2/RgWsPublic2', array( 'timeout' => 15, 'headers' => array( 'Content-Type' => 'application/soap+xml; charset=utf-8' ), 'body' => $env ) );
	if ( is_wp_error( $r ) ) {
		return null;
	}
	$body = wp_remote_retrieve_body( $r );
	$get  = function ( $tag ) use ( $body ) {
		return preg_match( '#<(?:\w+:)?' . $tag . '[^>]*>(.*?)</(?:\w+:)?' . $tag . '>#su', $body, $m ) ? trim( html_entity_decode( $m[1] ) ) : '';
	};
	if ( '' === $get( 'onomasia' ) ) {
		return null;
	}
	$deactivated = '2' === $get( 'deactivation_flag' );
	return array(
		'name'     => $get( 'onomasia' ),
		'address'  => trim( $get( 'postal_address' ) . ' ' . $get( 'postal_address_no' ) ),
		'postcode' => $get( 'postal_zip_code' ),
		'city'     => $get( 'postal_area_description' ),
		'doy'      => $get( 'doy_descr' ),
		'activity' => $get( 'firm_act_descr' ),
		'source'   => $deactivated ? 'ΑΑΔΕ (ανενεργό ΑΦΜ)' : 'ΑΑΔΕ',
	);
}

add_action( 'wp_ajax_ksilakia_afm', 'ksilakia_afm_ajax' );
add_action( 'wp_ajax_nopriv_ksilakia_afm', 'ksilakia_afm_ajax' );
function ksilakia_afm_ajax() {
	check_ajax_referer( 'ksilakia_afm', 'nonce' );
	$ip  = $_SERVER['REMOTE_ADDR'] ?? '';
	$rl  = 'ksilakia_afm_rl_' . md5( $ip );
	$hit = (int) get_transient( $rl );
	if ( $hit > 30 ) {
		wp_send_json_error( array( 'msg' => 'Πολλές αναζητήσεις. Δοκιμάστε ξανά σε λίγο.' ) );
	}
	set_transient( $rl, $hit + 1, 10 * MINUTE_IN_SECONDS );
	$res = ksilakia_afm_lookup( $_POST['afm'] ?? '' );
	if ( is_wp_error( $res ) ) {
		wp_send_json_error( array( 'msg' => $res->get_error_message(), 'code' => $res->get_error_code() ) );
	}
	wp_send_json_success( $res );
}

/* ------------------------------------ Checkout: Απόδειξη / Τιμολόγιο */

function ksilakia_invoice_fields() {
	return array(
		'billing_company'  => 'Επωνυμία',
		'billing_vat'      => 'ΑΦΜ',
		'billing_doy'      => 'ΔΟΥ',
		'billing_activity' => 'Δραστηριότητα',
	);
}

add_filter( 'woocommerce_billing_fields', function ( $f ) {
	$default = ksilakia_is_b2b() || get_user_meta( get_current_user_id(), 'billing_invoice_type', true ) === 'invoice' ? 'invoice' : 'receipt';
	$f['billing_invoice_type'] = array(
		'type'     => 'radio',
		'label'    => 'Παραστατικό',
		'required' => true,
		'options'  => array( 'receipt' => 'Απόδειξη', 'invoice' => 'Τιμολόγιο' ),
		'default'  => $default,
		'class'    => array( 'form-row-wide', 'invoice-type' ),
		'priority' => 25,
	);
	$f['billing_company'] = array_merge( $f['billing_company'] ?? array(), array( 'label' => 'Επωνυμία', 'required' => false, 'class' => array( 'form-row-wide', 'invoice-field' ), 'priority' => 27 ) );
	$f['billing_vat']      = array( 'label' => 'ΑΦΜ', 'required' => false, 'class' => array( 'form-row-first', 'invoice-field' ), 'priority' => 26, 'maxlength' => 9, 'input_class' => array( 'afm-input' ), 'custom_attributes' => array( 'inputmode' => 'numeric', 'data-afm-lookup' => '1', 'data-afm-map' => 'name:billing_company,doy:billing_doy,activity:billing_activity,address:billing_address_1,postcode:billing_postcode,city:billing_city' ) );
	$f['billing_doy']      = array( 'label' => 'ΔΟΥ', 'required' => false, 'class' => array( 'form-row-last', 'invoice-field' ), 'priority' => 26 );
	$f['billing_activity'] = array( 'label' => 'Δραστηριότητα', 'required' => false, 'class' => array( 'form-row-wide', 'invoice-field' ), 'priority' => 28 );
	return $f;
} );

add_action( 'woocommerce_after_checkout_validation', function ( $data, $errors ) {
	if ( ( $data['billing_invoice_type'] ?? 'receipt' ) !== 'invoice' ) {
		return;
	}
	foreach ( array( 'billing_company' => 'Επωνυμία', 'billing_vat' => 'ΑΦΜ', 'billing_doy' => 'ΔΟΥ' ) as $k => $label ) {
		if ( empty( $data[ $k ] ) ) {
			$errors->add( $k, "Για τιμολόγιο συμπληρώστε: $label." );
		}
	}
	$vat = preg_replace( '/\D/', '', $data['billing_vat'] ?? '' );
	if ( ! empty( $data['billing_vat'] ) && ( 9 !== strlen( $vat ) || ! ksilakia_afm_checksum( $vat ) ) ) {
		$errors->add( 'billing_vat_invalid', 'Το ΑΦΜ δεν είναι έγκυρο (9 ψηφία).' );
	}
}, 10, 2 );

// Receipt orders: drop stale invoice data so the order shows exactly what was requested.
add_action( 'woocommerce_checkout_create_order', function ( $order, $data ) {
	if ( ( $data['billing_invoice_type'] ?? 'receipt' ) !== 'invoice' ) {
		foreach ( array( '_billing_company', '_billing_vat', '_billing_doy', '_billing_activity' ) as $m ) {
			$order->delete_meta_data( $m );
		}
		$order->set_billing_company( '' );
	}
}, 10, 2 );

function ksilakia_order_invoice_rows( $order ) {
	$type = $order->get_meta( '_billing_invoice_type' ) ?: 'receipt';
	$rows = array( 'Παραστατικό' => 'invoice' === $type ? 'Τιμολόγιο' : 'Απόδειξη' );
	if ( 'invoice' === $type ) {
		foreach ( array( 'billing_vat' => 'ΑΦΜ', 'billing_doy' => 'ΔΟΥ', 'billing_activity' => 'Δραστηριότητα' ) as $k => $label ) {
			$v = $order->get_meta( '_' . $k );
			if ( $v ) {
				$rows[ $label ] = $v;
			}
		}
	}
	return $rows;
}

add_action( 'woocommerce_admin_order_data_after_billing_address', function ( $o ) {
	foreach ( ksilakia_order_invoice_rows( $o ) as $l => $v ) {
		echo '<p><strong>' . esc_html( $l ) . ':</strong> ' . esc_html( $v ) . '</p>';
	}
} );

add_filter( 'woocommerce_order_formatted_billing_address', function ( $addr, $order ) {
	if ( 'invoice' === $order->get_meta( '_billing_invoice_type' ) ) {
		$extra = array_filter( array( $order->get_meta( '_billing_vat' ) ? 'ΑΦΜ ' . $order->get_meta( '_billing_vat' ) : '', $order->get_meta( '_billing_doy' ) ? 'ΔΟΥ ' . $order->get_meta( '_billing_doy' ) : '' ) );
		if ( $extra && ! empty( $addr['company'] ) ) {
			$addr['company'] .= ' (' . implode( ', ', $extra ) . ')';
		}
	}
	return $addr;
}, 10, 2 );

add_action( 'woocommerce_email_after_order_table', function ( $order, $sent_to_admin, $plain ) {
	$rows = ksilakia_order_invoice_rows( $order );
	if ( $plain ) {
		foreach ( $rows as $l => $v ) {
			echo "$l: $v\n";
		}
		return;
	}
	echo '<table cellspacing="0" cellpadding="6" style="width:100%;margin-bottom:20px;border:1px solid #e5e5e5"><tbody>';
	foreach ( $rows as $l => $v ) {
		echo '<tr><th scope="row" style="text-align:left;border:1px solid #e5e5e5">' . esc_html( $l ) . '</th><td style="border:1px solid #e5e5e5">' . esc_html( $v ) . '</td></tr>';
	}
	echo '</tbody></table>';
}, 10, 3 );

add_action( 'woocommerce_order_details_after_customer_details', function ( $order ) {
	foreach ( ksilakia_order_invoice_rows( $order ) as $l => $v ) {
		echo '<tr><th>' . esc_html( $l ) . ':</th><td>' . esc_html( $v ) . '</td></tr>';
	}
} );

/* --------------------------------- Shipping: pickup only in Thessaloniki */

function ksilakia_is_thessaloniki_postcode( $pc ) {
	$pc = preg_replace( '/\D/', '', (string) $pc );
	return (bool) preg_match( '/^5[4-7]\d{3}$/', $pc );
}

add_filter( 'woocommerce_package_rates', function ( $rates, $package ) {
	$pc = $package['destination']['postcode'] ?? '';
	if ( ksilakia_is_thessaloniki_postcode( $pc ) ) {
		return $rates;
	}
	foreach ( $rates as $id => $rate ) {
		if ( 'local_pickup' === $rate->get_method_id() || 'pickup_location' === $rate->get_method_id() ) {
			unset( $rates[ $id ] );
		}
	}
	return $rates;
}, 10, 2 );

// Cash on delivery only for deliveries inside Greece.
add_filter( 'woocommerce_available_payment_gateways', function ( $gateways ) {
	if ( isset( $gateways['cod'] ) && WC()->customer && 'GR' !== WC()->customer->get_shipping_country() ) {
		unset( $gateways['cod'] );
	}
	return $gateways;
} );

/* -------------------------------------------------------- contact form */

add_action( 'wp_ajax_ksilakia_contact', 'ksilakia_contact_handler' );
add_action( 'wp_ajax_nopriv_ksilakia_contact', 'ksilakia_contact_handler' );
function ksilakia_contact_handler() {
	check_ajax_referer( 'ksilakia_contact', 'nonce' );
	if ( ! empty( $_POST['website'] ) ) {
		wp_send_json( array( 'ok' => true ) ); // honeypot
	}
	$name  = sanitize_text_field( wp_unslash( $_POST['name'] ?? '' ) );
	$phone = sanitize_text_field( wp_unslash( $_POST['phone'] ?? '' ) );
	$email = sanitize_email( wp_unslash( $_POST['email'] ?? '' ) );
	$size  = sanitize_text_field( wp_unslash( $_POST['size'] ?? '' ) );
	$msg   = sanitize_textarea_field( wp_unslash( $_POST['message'] ?? '' ) );
	if ( ! $name || ! $phone ) {
		wp_send_json( array( 'ok' => false, 'error' => 'Συμπληρώστε όνομα και τηλέφωνο.' ) );
	}
	$body    = "Όνομα/Επιχείρηση: $name\nΤηλέφωνο: $phone\nEmail: $email\nΔιάσταση: $size\n\n$msg";
	$headers = $email ? array( 'Reply-To: ' . $email ) : array();
	$sent    = wp_mail( get_option( 'admin_email' ), '[ksilakia.gr] Αίτημα προσφοράς από ' . $name, $body, $headers );
	wp_send_json( array( 'ok' => (bool) $sent, 'error' => $sent ? '' : 'Δεν έγινε αποστολή. Καλέστε μας στο ' . KSILAKIA_PHONE_DISPLAY . '.' ) );
}

/* -------------------------------------------------------------- SEO */

remove_action( 'wp_head', 'rel_canonical' );
add_action( 'template_redirect', function () {
	if ( is_404() && preg_match( '#^/(shop|products?|eshop)/?$#', wp_parse_url( $_SERVER['REQUEST_URI'], PHP_URL_PATH ) ) ) {
		wp_redirect( home_url( '/kalamakia-gia-souvlakia/' ), 301 );
		exit;
	}
} );
add_filter( 'wp_sitemaps_add_provider', fn( $p, $name ) => 'users' === $name ? false : $p, 10, 2 );
add_filter( 'wp_sitemaps_taxonomies', fn( $t ) => array_diff_key( $t, array( 'category' => 1, 'post_tag' => 1 ) ) );
add_filter( 'wp_sitemaps_posts_query_args', function ( $args, $type ) {
	if ( 'page' === $type ) {
		$args['post__not_in'] = array_filter( array( wc_get_page_id( 'cart' ), wc_get_page_id( 'checkout' ), wc_get_page_id( 'myaccount' ) ) );
	}
	return $args;
}, 10, 2 );
add_action( 'wp_head', function () {
	if ( is_404() || is_search() || is_cart() || is_checkout() || is_account_page() ) {
		echo '<meta name="robots" content="noindex,follow">' . "\n";
		if ( ! is_cart() && ! is_checkout() && ! is_account_page() ) {
			return;
		}
	}
	$desc = 'Καλαμάκια για σουβλάκια bamboo VN srl (ξυλάκια σουβλακιού) για ψητοπωλεία και σουβλακομηχανές, πιστοποιημένα CE, χωρίς χημικά. 215×3,2 / 215×4 / 240×4 mm σε σακούλα 1.000 ή κούτα 10.000 τεμ. Λιανική & χονδρική B2B σε όλη την Ελλάδα.';
	if ( is_singular() && ! is_front_page() ) {
		$post = get_queried_object();
		$desc = wp_strip_all_tags( has_excerpt( $post ) ? get_the_excerpt( $post ) : wp_trim_words( $post->post_content, 28, '…' ) );
	} elseif ( is_home() ) {
		$desc = 'Οδηγοί για καλαμάκια σουβλακιού, σουβλάκια και σουβλακομηχανές: ποια διάσταση ξυλακιού ταιριάζει σε κάθε σουβλάκι και μηχανή, αποθήκευση, πιστοποιήσεις και συμβουλές για ψητοπωλεία και βιοτεχνίες.';
	} elseif ( is_shop() || is_product_category() ) {
		$desc = 'Αγοράστε online καλαμάκια για σουβλάκια bamboo VN srl: 215×3,2, 215×4 και 240×4 mm. Σακούλα 1.000 τεμ. ή κούτα 10.000 τεμ. Τιμές λιανικής και χονδρικής για ψητοπωλεία, κρεοπωλεία και βιοτεχνίες.';
	}
	$url = is_front_page() ? home_url( '/' ) : ( is_singular() ? get_permalink() : ( is_home() ? get_permalink( get_option( 'page_for_posts' ) ) : home_url( add_query_arg( array() ) ) ) );
	$img = is_singular() && has_post_thumbnail() ? get_the_post_thumbnail_url( null, 'large' ) : get_template_directory_uri() . '/img/bamboo-01.jpg';
	echo '<meta name="description" content="' . esc_attr( $desc ) . '">' . "\n";
	echo '<link rel="canonical" href="' . esc_url( $url ) . '">' . "\n";
	echo '<meta property="og:locale" content="el_GR"><meta property="og:type" content="website"><meta property="og:site_name" content="ksilakia.gr">' . "\n";
	echo '<meta property="og:title" content="' . esc_attr( wp_get_document_title() ) . '"><meta property="og:description" content="' . esc_attr( $desc ) . '"><meta property="og:url" content="' . esc_url( $url ) . '"><meta property="og:image" content="' . esc_url( $img ) . '">' . "\n";
	echo '<meta name="twitter:card" content="summary_large_image">' . "\n";
	echo '<link rel="icon" href="' . esc_url( get_template_directory_uri() . '/img/favicon.svg' ) . '" type="image/svg+xml">' . "\n";
	if ( is_front_page() ) {
		$ld = array(
			'@context' => 'https://schema.org',
			'@graph'   => array(
				array(
					'@type'     => 'Organization',
					'@id'       => home_url( '/#org' ),
					'name'      => 'ksilakia.gr - ' . KSILAKIA_COMPANY,
					'url'       => home_url( '/' ),
					'logo'      => get_template_directory_uri() . '/img/favicon.svg',
					'telephone' => KSILAKIA_PHONE,
					'email'     => KSILAKIA_EMAIL,
					'address'   => array( '@type' => 'PostalAddress', 'streetAddress' => 'Μακεδονικού Αγώνα 19', 'addressLocality' => 'Παλαιόκαστρο, Θεσσαλονίκη', 'postalCode' => '570 13', 'addressCountry' => 'GR' ),
					'sameAs'    => array( 'https://crazysouvle.gr', 'https://insouvlaki.com', 'https://karvouno.gr', 'https://butcherequip.gr' ),
				),
				array( '@type' => 'WebSite', 'url' => home_url( '/' ), 'name' => 'ksilakia.gr', 'inLanguage' => 'el', 'publisher' => array( '@id' => home_url( '/#org' ) ) ),
				array(
					'@type'      => 'FAQPage',
					'mainEntity' => array_map( fn( $q ) => array( '@type' => 'Question', 'name' => $q[0], 'acceptedAnswer' => array( '@type' => 'Answer', 'text' => $q[1] ) ), ksilakia_faq() ),
				),
			),
		);
		echo '<script type="application/ld+json">' . wp_json_encode( $ld, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . '</script>' . "\n";
	} elseif ( is_singular( 'post' ) ) {
		$ld = array(
			'@context'         => 'https://schema.org',
			'@type'            => 'Article',
			'headline'         => get_the_title(),
			'description'      => $desc,
			'image'            => $img,
			'datePublished'    => get_the_date( 'c' ),
			'dateModified'     => get_the_modified_date( 'c' ),
			'inLanguage'       => 'el',
			'mainEntityOfPage' => $url,
			'author'           => array( '@type' => 'Organization', 'name' => 'ksilakia.gr', 'url' => home_url( '/' ) ),
			'publisher'        => array( '@type' => 'Organization', 'name' => 'ksilakia.gr', 'logo' => array( '@type' => 'ImageObject', 'url' => get_template_directory_uri() . '/img/favicon.svg' ) ),
		);
		echo '<script type="application/ld+json">' . wp_json_encode( $ld, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . '</script>' . "\n";
	}
}, 1 );

add_filter( 'document_title_separator', fn() => '|' );
add_filter( 'document_title_parts', function ( $t ) {
	if ( is_front_page() ) {
		return array( 'title' => 'Καλαμάκια & ξυλάκια για σουβλάκια bamboo VN — Λιανική & Χονδρική', 'site' => 'ksilakia.gr' );
	}
	if ( is_home() ) {
		$t['title'] = 'Οδηγοί για καλαμάκια, σουβλάκια & σουβλακομηχανές';
	}
	if ( function_exists( 'is_shop' ) && is_shop() ) {
		$t['title'] = 'Καλαμάκια για σουβλάκια — όλες οι διαστάσεις & συσκευασίες';
	}
	return $t;
} );

function ksilakia_faq() {
	return array(
		array( 'Τι διαφορετικό έχουν τα ξυλάκια της εταιρίας VN srl;', 'Ότι τα φτιάχνει ο ίδιος που φτιάχνει και τις σουβλακομηχανές. Η VN srl είναι ιταλική εταιρία μηχανών· τα καλαμάκια της βγήκαν επειδή οι πελάτες της είχαν εμπλοκές με ξυλάκια της αγοράς. Bamboo «Mao», ίδια διάμετρος σε όλα, λείο χωρίς σκλήθρες, CE, χωρίς χημικά.' ),
		array( 'Είναι κατάλληλα για μηχανή σουβλακιών;', 'Ναι, γι\' αυτό υπάρχουν. Δουλεύουν στις VN SM3000 και SM7000 και σε όποια άλλη μηχανή δέχεται 3,2 ή 4 mm. Αν δεν ξέρετε τι διάμετρο θέλει η δική σας, ρωτήστε μας. Μηχανές και σέρβις θα βρείτε στο crazysouvle.gr.' ),
		array( 'Έχουν πιστοποίηση για επαφή με τρόφιμα;', 'Ναι. CE, χωρίς λευκαντικά ή άλλα χημικά, αριθμός παρτίδας σε κάθε σακούλα. Καλύπτουν τα ευρωπαϊκά και τα καναδικά πρότυπα, οπότε δεν θα έχετε θέμα σε έλεγχο.' ),
		array( 'Ποια διάσταση να διαλέξω;', 'Για το κλασικό καλαμάκι, 215×3,2. Αν το σουβλάκι είναι πιο βαρύ ή βγαίνει από μηχανή, 215×4. Για μεγάλη μερίδα ή κοντοσούβλι, 240×4. Αν αμφιβάλλετε, πείτε μας πόσα γραμμάρια είναι η μερίδα και θα σας πούμε.' ),
		array( 'Πώς αγοράζω με τιμές χονδρικής (B2B);', 'Κάνετε εγγραφή, τσεκάρετε «Λογαριασμός B2B / χονδρικής» και βάζετε επωνυμία και ΑΦΜ. Το ελέγχουμε μέσα σε μία εργάσιμη και μετά βλέπετε τις τιμές χονδρικής όταν συνδέεστε.' ),
		array( 'Πώς συσκευάζονται και πόσα μπορώ να αγοράσω;', 'Σακουλάκι των 1.000 ή κούτα των 10.000 (δέκα σακουλάκια, κλεισμένα μαζί σε σακούλα MAP). Η κούτα βγαίνει αρκετά πιο φθηνά το τεμάχιο. Οι B2B πελάτες μπορούν να πάρουν και παλέτα.' ),
	);
}

/* ------------------------------------------------------ misc cleanup */

add_filter( 'wp_mail_from', fn() => KSILAKIA_EMAIL );
add_filter( 'wp_mail_from_name', fn() => 'ksilakia.gr' );

remove_action( 'wp_head', 'wp_generator' );

add_action( 'wp_head', function () {
	if ( is_admin() || ( is_user_logged_in() && current_user_can( 'manage_options' ) ) ) {
		return;
	}
	$id = esc_js( KSILAKIA_GA4_ID );
	echo '<script async src="https://www.googletagmanager.com/gtag/js?id=' . esc_attr( KSILAKIA_GA4_ID ) . '"></script>' . "\n";
	echo "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','{$id}');</script>\n";
}, 1 );
add_filter( 'the_generator', '__return_empty_string' );
add_filter( 'woocommerce_product_description_heading', '__return_empty_string' );
add_filter( 'wwp_filter_wholesale_price_title_text', function () { return 'Τιμή χονδρικής:'; } );
add_filter( 'gettext_woocommerce-wholesale-prices', function ( $t, $orig ) {
	$map = array( 'Wholesale Price:' => 'Τιμή χονδρικής:', 'Wholesale Price' => 'Τιμή χονδρικής', 'Retail Price' => 'Τιμή λιανικής' );
	return isset( $map[ $orig ] ) ? $map[ $orig ] : $t;
}, 10, 2 );
add_filter( 'woocommerce_product_additional_information_heading', '__return_empty_string' );

/* --------------------------------------- B2B: παλέτα & αποστολή */

function ksilakia_cart_is_box( $item ) {
	return isset( $item['variation']['attribute_pa_syskevasia'] )
		&& 'kouta-10000' === $item['variation']['attribute_pa_syskevasia'];
}

// Wholesale tier on box only: 5–29 κούτες −20%, 30+ (παλέτα) −25%, under 5 = λιανική.
add_filter( 'woocommerce_product_get_price', 'ksilakia_b2b_box_price', 20, 2 );
add_filter( 'woocommerce_product_variation_get_price', 'ksilakia_b2b_box_price', 20, 2 );
function ksilakia_b2b_box_price( $price, $product ) {
	if ( ! ksilakia_is_b2b() ) {
		return $price;
	}
	$attrs = $product->get_variation_attributes();
	if ( empty( $attrs['attribute_pa_syskevasia'] ) || 'kouta-10000' !== $attrs['attribute_pa_syskevasia'] ) {
		return $price;
	}
	$qty = 0;
	if ( WC()->cart ) {
		foreach ( WC()->cart->get_cart() as $item ) {
			if ( ksilakia_cart_is_box( $item ) ) {
				$qty += (int) $item['quantity'];
			}
		}
	}
	$reg = (float) $product->get_regular_price();
	if ( $qty >= 30 ) {
		return round( $reg * 0.75, 2 );
	}
	if ( $qty >= 5 ) {
		return round( $reg * 0.80, 2 );
	}
	return $reg;
}

// B2B shipping: only transport company, cost set after quote.
add_filter( 'woocommerce_package_rates', function ( $rates ) {
	if ( ! ksilakia_is_b2b() ) {
		return $rates;
	}
	return array(
		'b2b_transport' => new WC_Shipping_Rate(
			'b2b_transport',
			'Αποστολή με μεταφορική εταιρία (κόστος κατόπιν προσφοράς/συνεννόησης)',
			0,
			array(),
			'flat_rate',
			0
		),
	);
}, 20 );

// B2B pricing note on product page and cart.
add_action( 'woocommerce_single_product_summary', function () {
	if ( ksilakia_is_b2b() ) {
		echo '<p class="b2b-tier-note">Τιμή χονδρικής στην κούτα: <strong>−20%</strong> από 5 κούτες και πάνω · για παλέτα (30+ κούτες): <strong>−25%</strong>. Αποστολή με μεταφορική εταιρία κατόπιν προσφοράς.</p>';
	}
}, 25 );

add_action( 'woocommerce_before_cart', function () {
	if ( ksilakia_is_b2b() ) {
		wc_print_notice( 'Χονδρική: κούτα −20% από 5 κούτες και πάνω · για παλέτα (30+ κούτες) η τιμή της κούτας γίνεται −25%. Η αποστολή γίνεται με μεταφορική εταιρία, κατόπιν προσφοράς και συνεννόησης.', 'notice' );
	}
} );

// B2B payment: no online payment — order is a request; quote follows.
add_filter( 'woocommerce_available_payment_gateways', function ( $gateways ) {
	if ( ! ksilakia_is_b2b() ) {
		return $gateways;
	}
	return array_intersect_key( $gateways, array( 'bacs' => true ) );
} );

add_filter( 'woocommerce_gateway_title', function ( $title, $id ) {
	if ( ksilakia_is_b2b() && 'bacs' === $id ) {
		return 'Χωρίς online πληρωμή — θα λάβετε προσφορά με το κόστος μεταφορικής';
	}
	return $title;
}, 10, 2 );

add_filter( 'woocommerce_gateway_description', function ( $desc, $id ) {
	if ( ksilakia_is_b2b() && 'bacs' === $id ) {
		return '';
	}
	return $desc;
}, 10, 2 );

add_action( 'woocommerce_before_checkout_form', function () {
	if ( ksilakia_is_b2b() ) {
		wc_print_notice( 'Η παραγγελία καταχωρείται χωρίς πληρωμή. Θα λάβετε προσφορά με το κόστος μεταφορικής και το τελικό σύνολο.', 'notice' );
	}
}, 5 );

// B2B: hide PayPal express / card buttons, coupon field and free-shipping tag.
add_action( 'wp_head', function () {
	if ( ksilakia_is_b2b() ) {
		echo '<style>.ppc-button-container,#ppc-button,#ppc-button-ppcp-gateway,.woocommerce-PayPal,.ppcp-card-button,div[id*="ppc-button"],.wc-proceed-to-checkout .ppc-button-container,.wc-block-components-express-payment,.wc-block-components-totals-coupon,.wc-block-components-totals-coupon-link,.wc-block-components-totals-shipping .wc-block-components-totals-item__value,.wc-block-components-shipping-rates-control .wc-block-components-radio-control__secondary-label,.wc-block-components-shipping-rates-control .wc-block-components-formatted-money-amount,.cart-collaterals .coupon{display:none!important}</style>';
	}
} );

// B2B: prices shown net of VAT with «+ ΦΠΑ» suffix everywhere.
add_filter( 'option_woocommerce_tax_display_shop', function ( $v ) {
	return ksilakia_is_b2b() ? 'excl' : $v;
} );
add_filter( 'option_woocommerce_tax_display_cart', function ( $v ) {
	return ksilakia_is_b2b() ? 'excl' : $v;
} );
add_filter( 'woocommerce_get_price_suffix', function ( $suffix, $product ) {
	return ksilakia_is_b2b() ? ' +ΦΠΑ' : $suffix;
}, 10, 2 );

// B2B: no coupons (wholesale price is already discounted).
add_filter( 'woocommerce_coupons_enabled', function ( $enabled ) {
	return ksilakia_is_b2b() ? false : $enabled;
} );

// B2B: show transport-company label without the «ΔΩΡΕΑΝ» cost tag.
add_filter( 'woocommerce_cart_shipping_method_full_label', function ( $label, $method ) {
	if ( ksilakia_is_b2b() && 'b2b_transport' === $method->id ) {
		return $method->get_label();
	}
	return $label;
}, 10, 2 );
