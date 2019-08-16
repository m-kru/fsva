library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;

entity gbt_pattern_checker_tb is
end entity;

architecture tb_arch of gbt_pattern_checker_tb is

    constant CLK_PERIOD : time := 10 ns;
    signal clk   : std_logic := '0';
    signal rst_n : std_logic := '1';

    signal initial_value_i : std_logic_vector(19 downto 0) := (1 downto 0 => '1', others => '0');

    signal tx_data_o : std_logic_vector(83 downto 0);
    signal tx_extra_data_widebus_o : std_logic_vector(31 downto 0);

    signal checker_synced : std_logic;
    signal num_of_err_frames : unsigned(31 downto 0);

    signal rx_data_i : std_logic_vector(83 downto 0);
    signal error_vector : std_logic_vector(83 downto 0) := (others => '0');
begin

    clk <= not clk after CLK_PERIOD/2;

    gbt_pattern_generator_0 : entity work.gbt_pattern_generator
    port map (
        clk                      => clk,
        rst_n                    => rst_n,
        initial_value_i          => initial_value_i,
        tx_data_o                => tx_data_o,
        tx_extra_data_widebus_o  => tx_extra_data_widebus_o
    );

    gbt_pattern_checker_0 : entity work.gbt_pattern_checker
    generic map (
        NUM_FRAMES_TO_SYNC  => 3
    )
    port map (
        clk                      => clk,
        rst_n                    => rst_n,
        widebus_mode_i           => '1',
        rx_data_i                => rx_data_i,
        rx_extra_data_widebus_i  => tx_extra_data_widebus_o,
        synced_o                 => checker_synced,
        unsigned(num_of_err_frames_o) => num_of_err_frames
    );

    rx_data_i <= tx_data_o xor error_vector;

    main: process

        procedure apply_rst_n is
        begin
            rst_n <= '0';
            wait for CLK_PERIOD;
            rst_n <= '1';
        end procedure;

    begin
        wait for 2 * CLK_PERIOD;
        apply_rst_n;

        wait for 6 * CLK_PERIOD;
        assert checker_synced = '1' report "GBT pattern checker failed to synchronize!" severity failure;

        error_vector <= (0 => '1', others => '0');
        wait for 1 * CLK_PERIOD;
        error_vector <= (others => '0');
        wait for 1 * CLK_PERIOD;
        assert to_integer(num_of_err_frames) = 1 report "GBT pattern checker failed to detect an error!" severity failure;

        error_vector <= (83 => '1', others => '0');
        wait for 1 * CLK_PERIOD;
        error_vector <= (others => '0');
        wait for 1 * CLK_PERIOD;
        assert to_integer(num_of_err_frames) = 2 report "GBT pattern checker failed to detect an error in Slow Control Internal Control bit!" severity failure;

        wait for 2 * CLK_PERIOD;

        std.env.finish;

    end process;
end;
